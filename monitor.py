#!/usr/bin/env python3
"""
Redis Health Monitor
A diagnostic tool for Redis support engineers

Author: Valters Upenieks
Created for Redis Technical Support Engineer interview
"""

import redis
import time
import sys
from datetime import datetime

class RedisHealthMonitor:
    def __init__(self, host='localhost', port=6379):
        """Initialize Redis connection"""
        try:
            self.redis = redis.Redis(
                host=host,
                port=port,
                decode_responses=True,
                socket_connect_timeout=5
            )
            # Test connection
            self.redis.ping()
            print(f"✅ Connected to Redis at {host}:{port}\n")
        except redis.ConnectionError:
            print(f"❌ Cannot connect to Redis at {host}:{port}")
            print("   Make sure Redis is running: redis-server")
            sys.exit(1)
        except Exception as e:
            print(f"❌ Error connecting to Redis: {e}")
            sys.exit(1)

    def get_server_info(self):
        """Get basic server information"""
        info = self.redis.info('server')
        return {
            'version': info.get('redis_version', 'Unknown'),
            'os': info.get('os', 'Unknown'),
            'uptime_days': info.get('uptime_in_days', 0),
            'uptime_seconds': info.get('uptime_in_seconds', 0)
        }

    def get_memory_info(self):
        """Get memory statistics"""
        info = self.redis.info('memory')
        used_memory_mb = info.get('used_memory', 0) / (1024 * 1024)
        max_memory = info.get('maxmemory', 0)
        max_memory_mb = max_memory / (1024 * 1024) if max_memory > 0 else None
        
        return {
            'used_memory_mb': round(used_memory_mb, 2),
            'used_memory_human': info.get('used_memory_human', 'N/A'),
            'maxmemory_mb': round(max_memory_mb, 2) if max_memory_mb else 'Not set',
            'fragmentation_ratio': round(info.get('mem_fragmentation_ratio', 0), 2),
            'evicted_keys': info.get('evicted_keys', 0)
        }

    def get_stats(self):
        """Get performance statistics"""
        info = self.redis.info('stats')
        return {
            'total_connections': info.get('total_connections_received', 0),
            'total_commands': info.get('total_commands_processed', 0),
            'ops_per_sec': info.get('instantaneous_ops_per_sec', 0),
            'rejected_connections': info.get('rejected_connections', 0),
            'keyspace_hits': info.get('keyspace_hits', 0),
            'keyspace_misses': info.get('keyspace_misses', 0)
        }

    def get_hit_rate(self, stats):
        """Calculate cache hit rate"""
        hits = stats['keyspace_hits']
        misses = stats['keyspace_misses']
        total = hits + misses
        
        if total == 0:
            return 0.0
        
        return round((hits / total) * 100, 2)

    def get_clients_info(self):
        """Get connected clients information"""
        info = self.redis.info('clients')
        return {
            'connected_clients': info.get('connected_clients', 0),
            'blocked_clients': info.get('blocked_clients', 0),
            'max_clients': info.get('maxclients', 10000)
        }

    def get_replication_info(self):
        """Get replication status"""
        info = self.redis.info('replication')
        role = info.get('role', 'unknown')
        
        result = {'role': role}
        
        if role == 'master':
            result['connected_slaves'] = info.get('connected_slaves', 0)
        elif role == 'slave':
            result['master_link_status'] = info.get('master_link_status', 'unknown')
            result['master_host'] = info.get('master_host', 'unknown')
        
        return result

    def get_slow_log(self, count=5):
        """Get recent slow queries"""
        try:
            slow_log = self.redis.slowlog_get(count)
            return slow_log
        except Exception as e:
            return []

    def get_persistence_info(self):
        """Get persistence configuration"""
        info = self.redis.info('persistence')
        return {
            'rdb_enabled': info.get('rdb_bgsave_in_progress', 0) == 0,
            'rdb_last_save': info.get('rdb_last_save_time', 0),
            'aof_enabled': info.get('aof_enabled', 0) == 1,
            'aof_rewrite_in_progress': info.get('aof_rewrite_in_progress', 0) == 1
        }

    def check_health(self):
        """Perform health checks and return warnings"""
        warnings = []
        
        # Check memory
        memory = self.get_memory_info()
        if memory['fragmentation_ratio'] > 1.5:
            warnings.append(f"⚠️  High memory fragmentation: {memory['fragmentation_ratio']}")
        
        if memory['evicted_keys'] > 0:
            warnings.append(f"⚠️  Keys being evicted: {memory['evicted_keys']}")
        
        # Check clients
        clients = self.get_clients_info()
        client_usage = (clients['connected_clients'] / clients['max_clients']) * 100
        if client_usage > 80:
            warnings.append(f"⚠️  High client usage: {client_usage:.1f}%")
        
        # Check hit rate
        stats = self.get_stats()
        hit_rate = self.get_hit_rate(stats)
        if hit_rate < 80 and (stats['keyspace_hits'] + stats['keyspace_misses']) > 100:
            warnings.append(f"⚠️  Low cache hit rate: {hit_rate}%")
        
        # Check replication
        repl = self.get_replication_info()
        if repl['role'] == 'slave' and repl.get('master_link_status') != 'up':
            warnings.append(f"❌ Replication link DOWN!")
        
        return warnings

    def display_dashboard(self):
        """Display formatted health dashboard"""
        # Clear screen (works on Unix/Linux/Mac)
        print("\033[H\033[J", end="")
        
        print("=" * 70)
        print("           🔴 REDIS HEALTH MONITOR")
        print("           Built by Valters Upenieks for Redis Interview")
        print("=" * 70)
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        # Server Info
        server = self.get_server_info()
        print("📊 SERVER INFORMATION")
        print(f"   Redis Version: {server['version']}")
        print(f"   OS: {server['os']}")
        print(f"   Uptime: {server['uptime_days']} days ({server['uptime_seconds']} seconds)")
        print()

        # Memory Info
        memory = self.get_memory_info()
        print("💾 MEMORY USAGE")
        print(f"   Used Memory: {memory['used_memory_human']} ({memory['used_memory_mb']} MB)")
        print(f"   Max Memory: {memory['maxmemory_mb']}")
        print(f"   Fragmentation Ratio: {memory['fragmentation_ratio']}")
        print(f"   Evicted Keys: {memory['evicted_keys']}")
        print()

        # Stats
        stats = self.get_stats()
        hit_rate = self.get_hit_rate(stats)
        print("⚡ PERFORMANCE STATS")
        print(f"   Operations/sec: {stats['ops_per_sec']}")
        print(f"   Total Commands: {stats['total_commands']:,}")
        print(f"   Total Connections: {stats['total_connections']:,}")
        print(f"   Cache Hit Rate: {hit_rate}%")
        print(f"   Rejected Connections: {stats['rejected_connections']}")
        print()

        # Clients
        clients = self.get_clients_info()
        print("👥 CONNECTED CLIENTS")
        print(f"   Connected: {clients['connected_clients']}")
        print(f"   Blocked: {clients['blocked_clients']}")
        print(f"   Max Clients: {clients['max_clients']}")
        print()

        # Replication
        repl = self.get_replication_info()
        print("🔄 REPLICATION")
        print(f"   Role: {repl['role'].upper()}")
        if repl['role'] == 'master':
            print(f"   Connected Slaves: {repl.get('connected_slaves', 0)}")
        elif repl['role'] == 'slave':
            print(f"   Master: {repl.get('master_host', 'N/A')}")
            print(f"   Link Status: {repl.get('master_link_status', 'N/A')}")
        print()

        # Persistence
        persist = self.get_persistence_info()
        print("💿 PERSISTENCE")
        print(f"   RDB Enabled: {'Yes' if persist['rdb_enabled'] else 'No'}")
        if persist['rdb_last_save'] > 0:
            last_save = datetime.fromtimestamp(persist['rdb_last_save'])
            print(f"   Last RDB Save: {last_save.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   AOF Enabled: {'Yes' if persist['aof_enabled'] else 'No'}")
        print()

        # Slow Log
        slow_queries = self.get_slow_log(5)
        if slow_queries:
            print("🐌 RECENT SLOW QUERIES (>10ms)")
            for i, query in enumerate(slow_queries[:5], 1):
                duration_ms = query['duration'] / 1000  # Convert to milliseconds
                command = ' '.join(str(arg) for arg in query['command'])
                print(f"   {i}. {duration_ms:.2f}ms - {command[:60]}")
            print()

        # Health Warnings
        warnings = self.check_health()
        if warnings:
            print("⚠️  HEALTH WARNINGS")
            for warning in warnings:
                print(f"   {warning}")
            print()
        else:
            print("✅ ALL HEALTH CHECKS PASSED")
            print()

        print("=" * 70)
        print("Press Ctrl+C to exit | Refreshes every 5 seconds")
        print("=" * 70)

    def monitor_continuous(self, interval=5):
        """Continuously monitor Redis"""
        try:
            while True:
                self.display_dashboard()
                time.sleep(interval)
        except KeyboardInterrupt:
            print("\n\n👋 Monitoring stopped. Goodbye!")
            sys.exit(0)

    def run_once(self):
        """Run monitor once (non-continuous)"""
        self.display_dashboard()

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Redis Health Monitor')
    parser.add_argument('--host', default='localhost', help='Redis host (default: localhost)')
    parser.add_argument('--port', type=int, default=6379, help='Redis port (default: 6379)')
    parser.add_argument('--once', action='store_true', help='Run once instead of continuous')
    parser.add_argument('--interval', type=int, default=5, help='Refresh interval in seconds (default: 5)')
    
    args = parser.parse_args()
    
    # Create monitor
    monitor = RedisHealthMonitor(host=args.host, port=args.port)
    
    # Run
    if args.once:
        monitor.run_once()
    else:
        monitor.monitor_continuous(interval=args.interval)

if __name__ == '__main__':
    main()
