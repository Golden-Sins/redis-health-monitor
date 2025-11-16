#!/bin/bash

# Redis Health Check Script
# Author: Valters Upenieks
# For Redis Technical Support Engineer Interview

echo "======================================"
echo "    🔴 REDIS HEALTH CHECK"
echo "    Quick Diagnostic Tool"
echo "======================================"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check if Redis is running
check_redis_running() {
    echo "1️⃣  Checking if Redis is running..."
    if pgrep -x redis-server > /dev/null; then
        echo -e "   ${GREEN}✅ Redis is running${NC}"
        return 0
    else
        echo -e "   ${RED}❌ Redis is NOT running${NC}"
        echo "   Start Redis with: redis-server"
        return 1
    fi
}

# Function to test connectivity
test_connection() {
    echo ""
    echo "2️⃣  Testing Redis connection..."
    if redis-cli ping > /dev/null 2>&1; then
        echo -e "   ${GREEN}✅ Redis responding to PING${NC}"
        return 0
    else
        echo -e "   ${RED}❌ Redis not responding${NC}"
        return 1
    fi
}

# Function to check memory
check_memory() {
    echo ""
    echo "3️⃣  Memory Usage:"
    redis-cli INFO memory | grep -E 'used_memory_human|maxmemory_human|mem_fragmentation_ratio' | while read line; do
        echo "   $line"
    done
    
    # Check fragmentation
    FRAG=$(redis-cli INFO memory | grep mem_fragmentation_ratio | cut -d: -f2 | tr -d '\r\n ')
    if (( $(echo "$FRAG > 1.5" | bc -l) )); then
        echo -e "   ${YELLOW}⚠️  High memory fragmentation: $FRAG${NC}"
    fi
}

# Function to check performance
check_performance() {
    echo ""
    echo "4️⃣  Performance:"
    OPS=$(redis-cli INFO stats | grep instantaneous_ops_per_sec | cut -d: -f2 | tr -d '\r\n ')
    echo "   Operations/sec: $OPS"
    
    CLIENTS=$(redis-cli INFO clients | grep connected_clients | cut -d: -f2 | tr -d '\r\n ')
    echo "   Connected clients: $CLIENTS"
}

# Function to check slow log
check_slow_log() {
    echo ""
    echo "5️⃣  Recent Slow Queries:"
    SLOW_COUNT=$(redis-cli SLOWLOG LEN)
    
    if [ "$SLOW_COUNT" -gt 0 ]; then
        echo -e "   ${YELLOW}⚠️  Found $SLOW_COUNT slow queries${NC}"
        echo "   Run: redis-cli SLOWLOG GET 10"
    else
        echo -e "   ${GREEN}✅ No slow queries detected${NC}"
    fi
}

# Function to check replication
check_replication() {
    echo ""
    echo "6️⃣  Replication Status:"
    ROLE=$(redis-cli INFO replication | grep role | cut -d: -f2 | tr -d '\r\n ')
    echo "   Role: $ROLE"
    
    if [ "$ROLE" = "slave" ]; then
        LINK=$(redis-cli INFO replication | grep master_link_status | cut -d: -f2 | tr -d '\r\n ')
        echo "   Master link: $LINK"
        
        if [ "$LINK" != "up" ]; then
            echo -e "   ${RED}❌ Replication link is DOWN!${NC}"
        fi
    fi
}

# Function to check disk space
check_disk() {
    echo ""
    echo "7️⃣  Disk Space:"
    df -h / | tail -1 | awk '{print "   Root partition: "$5" used ("$3" / "$2")"}'
    
    # Check Redis data directory if exists
    if [ -d "/var/lib/redis" ]; then
        du -sh /var/lib/redis 2>/dev/null | awk '{print "   Redis data size: "$1}'
    fi
}

# Main execution
main() {
    check_redis_running
    RUNNING=$?
    
    if [ $RUNNING -eq 0 ]; then
        test_connection
        if [ $? -eq 0 ]; then
            check_memory
            check_performance
            check_slow_log
            check_replication
            check_disk
        fi
    fi
    
    echo ""
    echo "======================================"
    echo "For detailed info: redis-cli INFO"
    echo "For monitoring: python3 monitor.py"
    echo "======================================"
}

# Run main function
main
