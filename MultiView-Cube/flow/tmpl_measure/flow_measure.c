#include <uapi/linux/ptrace.h>
#include <net/sock.h>
#include <bcc/proto.h>
#include <linux/bpf.h>

#define ETH_DOT1Q
#define IP_TCP 6
#define IP_UDP 17
#define IP_ICMP4 1

#define ETH_HLEN 14
#define DOT1Q_HLEN 4
#define UDP_HLEN 8
#define ICMP4_HLEN 8
#define VXLAN_HLEN 8

struct flow_tuple_t {
    u32 dip;
    u32 sip;
    u16 dport;
    u16 sport;
    u8 proto;
};

struct flow_stat_t{
    u64 start_ts;
    u64 last_ts;
    //
    u32 pkt_cnt;
    u16 pkt_bytes_min;
    u16 pkt_bytes_max;
    u32 pkt_bytes_total;
    //
    u32 ipat_min;    // ipat = inter-packet arrival time
    u32 ipat_max;
    u64 ipat_total;
    //
    u16 tcp_syn_cnt;
    u16 tcp_ack_cnt;
    u16 tcp_fin_cnt;
    u16 tcp_rst_cnt;
    u16 tcp_psh_cnt;
    u16 tcp_urg_cnt;

//    u32 tcp_cwr_cnt;
//    u32 tcp_ece_cnt;
};

BPF_HASH(<map_name>, struct flow_tuple_t, struct flow_stat_t); // let's try to save the number of IPs in here
//BPF_HASH(MAPNAME, struct flow_tuple_t, struct flow_stat_t);

int flow_measure(struct __sk_buff *skb) {
    u64 cur_time = bpf_ktime_get_ns();
//    bpf_trace_printk("%llu => Start packet_measure() \n", cur_time);
    u8 *cursor = 0;

    struct flow_tuple_t flow_tuple = {0};

    u32 pkt_len = 0;
    u8 tcp_urg = 0, tcp_ack = 0, tcp_psh = 0, tcp_rst = 0, tcp_syn = 0, tcp_fin = 0;
//    u8 tcp_cwr = 0, tcp_ece = 0;

    ETH: {
//        bpf_trace_printk("ETH \n");
        struct ethernet_t *ethernet = cursor_advance(cursor, sizeof(*ethernet));  // ethernet header (frame)
        pkt_len += ETH_HLEN;

        //filter IP packets (ethernet type = 0x0800) 0x0800 is IPv4 packet
        switch(ethernet->type){
            case ETH_P_8021Q:   goto DOT1Q;
            case ETH_P_IP:      goto IPV4;
            default:            goto DROP;
        }
    }

    DOT1Q: {
//        bpf_trace_printk("DOT1Q \n");
        struct dot1q_t *dot1q = cursor_advance(cursor, sizeof(*dot1q));
        pkt_len += DOT1Q_HLEN;

        goto IPV4;
    }

    IPV4: {
//        bpf_trace_printk("IPV4 \n");
        struct ip_t *ip = cursor_advance(cursor, sizeof(*ip));	// IP header (datagram)
        /*
          calculate ip header length
          value to multiply * 4
          e.g. ip->hlen = 5 ; IP Header Length = 5 x 4 byte = 20 byte
          The minimum value for this field is 5, which indicates a length of 5 x 32 bits(4 bytes) = 20 bytes
        */
        pkt_len += ip->tlen;

        flow_tuple.dip = ip -> dst;
        flow_tuple.sip = ip -> src;
        flow_tuple.proto = ip -> nextp;

        switch(flow_tuple.proto){
            case IP_TCP:    goto TCP;
            case IP_UDP:    goto UDP;
            case IP_ICMP4:  goto ICMP4;
            default:        goto DROP;
        }
    }

    ICMP4: {
//        bpf_trace_printk("ICMP4 \n");
        flow_tuple.dport = 0;
        flow_tuple.sport = 0;

        goto STORE;
    }

    UDP: {
//        bpf_trace_printk("UDP \n");
        struct udp_t *udp = cursor_advance(cursor, sizeof(*udp));

        flow_tuple.dport = udp -> dport;
        flow_tuple.sport = udp -> sport;

        goto STORE;
    }

    TCP: {
    //        bpf_trace_printk("TCP \n");
        struct tcp_t *tcp = cursor_advance(cursor, sizeof(*tcp));
        /*
          calculate tcp header length
          value to multiply *4
          e.g. tcp->offset = 5 ; TCP Header Length = 5 x 4 byte = 20 byte
          The minimum value for this field is 5, which indicates a length of 5 x 32 bits(4 bytes) = 20 bytes
        */

        flow_tuple.dport = tcp -> dst_port;
        flow_tuple.sport = tcp -> src_port;

//        tcp_cwr = tcp -> flag_cwr;
//        tcp_ece = tcp -> flag_ece;
        tcp_urg = tcp -> flag_urg;
        tcp_ack = tcp -> flag_ack;
        tcp_psh = tcp -> flag_psh;
        tcp_rst = tcp -> flag_rst;
        tcp_syn = tcp -> flag_syn;
        tcp_fin = tcp -> flag_fin;

        goto STORE;
    }

	STORE: {
//	    bpf_trace_printk("STORE \n");
	    // Look up the map to find a flow entry having same tuples

	    struct flow_stat_t *flow_stat = <map_name>.lookup(&flow_tuple); // this prevents transmitted packets from being counted
//	    struct flow_stat_t *flow_stat = MAPNAME.lookup(&flow_tuple); // this prevents transmitted packets from being counted
	    if (flow_stat) {
	        bpf_trace_printk("Found a matched flow from the map \n");
            u64 cur_ipat = cur_time - flow_stat->last_ts;

            flow_stat->last_ts = cur_time;
            flow_stat->pkt_cnt += 1;

            if(pkt_len < flow_stat->pkt_bytes_min) flow_stat->pkt_bytes_min = pkt_len;
            if(pkt_len > flow_stat->pkt_bytes_max) flow_stat->pkt_bytes_max = pkt_len;
            flow_stat->pkt_bytes_total += pkt_len;

            if (cur_ipat == 0 || cur_ipat < flow_stat->ipat_min) flow_stat->ipat_min = cur_ipat;
            if (cur_ipat == 0 || cur_ipat > flow_stat->ipat_max) flow_stat->ipat_max = cur_ipat;
            flow_stat->ipat_total += cur_ipat;

            if (tcp_syn) flow_stat->tcp_syn_cnt += 1;
            if (tcp_ack) flow_stat->tcp_ack_cnt += 1;
            if (tcp_fin) flow_stat->tcp_fin_cnt += 1;
            if (tcp_rst) flow_stat->tcp_rst_cnt += 1;
            if (tcp_psh) flow_stat->tcp_psh_cnt += 1;
            if (tcp_urg) flow_stat->tcp_urg_cnt += 1;

            goto EOP;
        } else {
        //    bpf_trace_printk("Cannot found a matched flow from the map \n");

            struct flow_stat_t new_flow_stat = {0};
            new_flow_stat.start_ts = cur_time;
            new_flow_stat.last_ts = cur_time;
            new_flow_stat.pkt_cnt = 1;
            new_flow_stat.pkt_bytes_min = pkt_len;
            new_flow_stat.pkt_bytes_max = pkt_len;
            new_flow_stat.pkt_bytes_total = pkt_len;
            new_flow_stat.ipat_min = 0;
            new_flow_stat.ipat_max = 0;
            new_flow_stat.ipat_total = 0;
            new_flow_stat.tcp_syn_cnt = tcp_syn;
            new_flow_stat.tcp_ack_cnt = tcp_ack;
            new_flow_stat.tcp_fin_cnt = tcp_fin;
            new_flow_stat.tcp_rst_cnt = tcp_rst;
            new_flow_stat.tcp_psh_cnt = tcp_psh;
            new_flow_stat.tcp_urg_cnt = tcp_urg;

            <map_name>.insert(&flow_tuple, &new_flow_stat);
//            MAPNAME.insert(&flow_tuple, &new_flow_stat);
            goto EOP;
        }
    }

    EOP:
//        bpf_trace_printk("EOP \n\n");
        return 0;

	DROP:
//	    bpf_trace_printk("DROP \n\n");
        return -1;
}
