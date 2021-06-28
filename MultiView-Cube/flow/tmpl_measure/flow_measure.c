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
    u64 pkt_bytes_sqr_total;
    //
    u32 ipat_min;    // ipat = inter-packet arrival time
    u32 ipat_max;
    u64 ipat_total;
    u64 ipat_sqr_total;
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

BPF_HASH(<map_name>, struct flow_tuple_t, struct flow_stat_t, 102400); // let's try to save the number of IPs in here

int flow_measure(struct __sk_buff *skb) {
    u64 cur_time = bpf_ktime_get_ns() / 1000;
    u8 *cursor = 0;

    struct flow_tuple_t flow_tuple = {0};

    u32 pkt_len = 0;
    // u32 payload_len = 0;
    u8 tcp_urg = 0, tcp_ack = 0, tcp_psh = 0, tcp_rst = 0, tcp_syn = 0, tcp_fin = 0;
//    u8 tcp_cwr = 0, tcp_ece = 0;

    ETH: {
        struct ethernet_t *ethernet = cursor_advance(cursor, sizeof(*ethernet));  // ethernet header (frame)
        // pkt_len += ETH_HLEN;

        //filter IP packets (ethernet type = 0x0800) 0x0800 is IPv4 packet
        switch(ethernet->type){
            case ETH_P_8021Q:   goto DOT1Q;
            case ETH_P_IP:      goto IPV4;
            default:            goto DROP;
        }
    }

    DOT1Q: {
        struct dot1q_t *dot1q = cursor_advance(cursor, sizeof(*dot1q));
        // pkt_len += DOT1Q_HLEN;

        goto IPV4;
    }

    IPV4: {
        struct ip_t *ip = cursor_advance(cursor, sizeof(*ip));	// IP header (datagram)
        /*
          calculate ip header length
          value to multiply * 4
          e.g. ip->hlen = 5 ; IP Header Length = 5 x 4 byte = 20 byte
          The minimum value for this field is 5, which indicates a length of 5 x 32 bits(4 bytes) = 20 bytes
        */
        // pkt_len += ip->tlen;
        pkt_len += ip->tlen - (ip->hlen * 4);

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
        pkt_len -= ICMP4_HLEN;
        flow_tuple.dport = 0;
        flow_tuple.sport = 0;

        goto STORE;
    }

    UDP: {
        struct udp_t *udp = cursor_advance(cursor, sizeof(*udp));

        pkt_len -= UDP_HLEN;
        flow_tuple.dport = udp -> dport;
        flow_tuple.sport = udp -> sport;

        goto STORE;
    }

    TCP: {
        struct tcp_t *tcp = cursor_advance(cursor, sizeof(*tcp));
        /*
          calculate tcp header length
          value to multiply *4
          e.g. tcp->offset = 5 ; TCP Header Length = 5 x 4 byte = 20 byte
          The minimum value for this field is 5, which indicates a length of 5 x 32 bits(4 bytes) = 20 bytes
        */
        pkt_len -= (tcp->offset * 4);
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
	    struct flow_stat_t *flow_stat = <map_name>.lookup(&flow_tuple); // this prevents transmitted packets from being counted
	    if (flow_stat) {
            u64 cur_ipat = cur_time - flow_stat->last_ts;

            flow_stat->last_ts = cur_time;
            flow_stat->pkt_cnt += 1;

            if(pkt_len < flow_stat->pkt_bytes_min) flow_stat->pkt_bytes_min = pkt_len;
            if(pkt_len > flow_stat->pkt_bytes_max) flow_stat->pkt_bytes_max = pkt_len;
            flow_stat->pkt_bytes_total += pkt_len;
            flow_stat->pkt_bytes_sqr_total += (pkt_len * pkt_len);

            if (flow_stat->ipat_min == 0 || cur_ipat < flow_stat->ipat_min) flow_stat->ipat_min = cur_ipat;
            if (flow_stat->ipat_max == 0 || cur_ipat > flow_stat->ipat_max) flow_stat->ipat_max = cur_ipat;
            flow_stat->ipat_total += cur_ipat;
            flow_stat->ipat_sqr_total += (cur_ipat * cur_ipat);

            if (tcp_syn) flow_stat->tcp_syn_cnt += 1;
            if (tcp_ack) flow_stat->tcp_ack_cnt += 1;
            if (tcp_fin) flow_stat->tcp_fin_cnt += 1;
            if (tcp_rst) flow_stat->tcp_rst_cnt += 1;
            if (tcp_psh) flow_stat->tcp_psh_cnt += 1;
            if (tcp_urg) flow_stat->tcp_urg_cnt += 1;

            goto EOP;
        } else {
            struct flow_stat_t new_flow_stat = {0};
            new_flow_stat.start_ts = cur_time;
            new_flow_stat.last_ts = cur_time;
            new_flow_stat.pkt_cnt = 1;
            new_flow_stat.pkt_bytes_min = pkt_len;
            new_flow_stat.pkt_bytes_max = pkt_len;
            new_flow_stat.pkt_bytes_total = pkt_len;
            new_flow_stat.pkt_bytes_sqr_total = (pkt_len * pkt_len);
            new_flow_stat.ipat_min = 0;
            new_flow_stat.ipat_max = 0;
            new_flow_stat.ipat_total = 0;
            new_flow_stat.ipat_sqr_total = 0;
            new_flow_stat.tcp_syn_cnt = tcp_syn;
            new_flow_stat.tcp_ack_cnt = tcp_ack;
            new_flow_stat.tcp_fin_cnt = tcp_fin;
            new_flow_stat.tcp_rst_cnt = tcp_rst;
            new_flow_stat.tcp_psh_cnt = tcp_psh;
            new_flow_stat.tcp_urg_cnt = tcp_urg;

            <map_name>.insert(&flow_tuple, &new_flow_stat);
            goto EOP;
        }
    }

    EOP:
        return 0;

	DROP:
        return -1;
}
