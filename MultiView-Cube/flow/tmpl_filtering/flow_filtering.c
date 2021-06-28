#define KBUILD_MODNAME "flow_filtering"

#include <linux/bpf.h> // Defining BPF-related values such as XDP_PASS
#include <linux/if_ether.h> // Defining Ethernet header format
#include <linux/in.h> // Defining IP Protocols (IPPROTO_*)
#include <linux/ip.h> // Defining IP Header format
#include <linux/tcp.h> // Defining TCP Header format
#include <linux/udp.h> // Defining UDP header format
#include <linux/icmp.h> // Defining ICMPv4 Header format

struct flow_tuple_t{
    uint32_t dip;
    uint32_t sip;
    uint16_t dport;
    uint16_t sport;
    uint8_t proto;
};

BPF_PERF_OUTPUT(events);
BPF_HASH(<map_name>, uint8_t, struct flow_tuple_t);

static bool is_matched(struct flow_tuple_t flow_tuple, struct flow_tuple_t* rule){
    if (rule->dip == 0 || rule->dip == flow_tuple.dip){ // Destination IP
        if (rule->sip == 0 || rule->sip == flow_tuple.sip){ // Source IP
            if (rule->dport == 0 || rule->dport == flow_tuple.dport){ // Destination Port
                if (rule->sport == 0 || rule->sport == flow_tuple.sport){ // Source Port
                    if (rule->proto == 0 || rule->proto == flow_tuple.proto){ // Protocol
                        // events.perf_submit(ctx, rule, sizeof(*rule));
                        return true;
                    }
                }
            }
        }
    }
    return false;
}

int flow_filtering(struct xdp_md *ctx) {
    void* pkt_start = (void *)(long)ctx->data;
    void* pkt_end = (void *)(long)ctx->data_end;

    struct flow_tuple_t flow_tuple = {0};
    struct ethhdr *eth = pkt_start;
    if ((void *)eth + sizeof(*eth) <= pkt_end){
        // Ethernet Packet
        
        struct iphdr *ip = pkt_start + sizeof(*eth);
        if ((void *)ip + sizeof(*ip) <= pkt_end){
            // IP Packet
            flow_tuple.dip = ntohl(ip->daddr);
            flow_tuple.sip = ntohl(ip->saddr);
            flow_tuple.proto = ip->protocol;

            if (ip->protocol == IPPROTO_ICMP){
                // ICMP Packet
                flow_tuple.dport = 0;
                flow_tuple.sport = 0;

            } else if (ip->protocol == IPPROTO_TCP){
                struct tcphdr *tcp = (void *)ip + sizeof(*ip);
                if ((void *)tcp + sizeof(*tcp) <= pkt_end){
                    // TCP Packet
                    flow_tuple.dport = ntohs(tcp->dest);
                    flow_tuple.sport = ntohs(tcp->source);
                }

            } else if(ip->protocol == IPPROTO_UDP){
                struct udphdr *udp = (void *)ip + sizeof(*ip);
                if ((void *)udp + sizeof(*udp) <= pkt_end){
                    // UDP Packet
                    flow_tuple.dport = ntohs(udp->dest);
                    flow_tuple.sport = ntohs(udp->dest);
                }
            }
        }
    }

    uint8_t i = 1;
    struct flow_tuple_t* rule = <map_name>.lookup(&i);
    if (rule == NULL){
        return XDP_PASS;
    }
    else{
        if (is_matched(flow_tuple, rule)) {
            events.perf_submit(ctx, &flow_tuple, sizeof(flow_tuple));
            return XDP_DROP;
        }
    }

    i = 2;
    rule = <map_name>.lookup(&i);
    if (rule == NULL){
        return XDP_PASS;
    }
    else{
        if (is_matched(flow_tuple, rule)) {
            events.perf_submit(ctx, &flow_tuple, sizeof(flow_tuple));
            return XDP_DROP;
        }
    }

    i = 3;
    rule = <map_name>.lookup(&i);
    if (rule == NULL){
        return XDP_PASS;
    }
    else{
        if (is_matched(flow_tuple, rule)) {
            events.perf_submit(ctx, &flow_tuple, sizeof(flow_tuple));
            return XDP_DROP;
        }
    }

    
    // uint8_t i = 1;
    // struct flow_tuple_t* rule = <map_name>.lookup(&rule_idx);
    // if (rule != NULL){
    //     if (rule->dip == 0 || rule->dip == flow_tuple.dip){ // Destination IP
    //         if (rule->sip == 0 || rule->sip == flow_tuple.sip){ // Source IP
    //             if (rule->dport == 0 || rule->dport == flow_tuple.dport){ // Destination Port
    //                 if (rule->sport == 0 || rule->sport == flow_tuple.sport){ // Source Port
    //                     if (rule->proto == 0 || rule->proto == flow_tuple.proto){ // Protocol
    //                         // events.perf_submit(ctx, rule, sizeof(*rule));
    //                         events.perf_submit(ctx, &flow_tuple, sizeof(flow_tuple));
    //                         return true;
    //                     }
    //                 }
    //             }
    //         }
    //     }
    // }
    return XDP_PASS;
}
