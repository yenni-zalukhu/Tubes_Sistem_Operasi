from flask import Flask, render_template, request, jsonify
import json
import base64
import io
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from copy import deepcopy
from typing import List, Dict

app = Flask(__name__)

class Process:
    def __init__(self, pid: int, arrival_time: int, burst_time: int, priority: int = 0):
        self.pid = pid
        self.arrival_time = arrival_time
        self.arrival = arrival_time  # Alias untuk kompatibilitas
        self.burst_time = burst_time
        self.burst = burst_time  # Alias untuk kompatibilitas
        self.priority = priority
        self.remaining_time = burst_time
        self.remaining = burst_time  # Alias untuk kompatibilitas
        self.completion_time = 0
        self.turnaround_time = 0
        self.waiting_time = 0
        self.response_time = -1
        self.start_time = -1

    def __str__(self):
        return f"P{self.pid}(AT:{self.arrival_time}, BT:{self.burst_time}, Priority:{self.priority})"

class CPUScheduler:
    def __init__(self):
        self.processes = []
    
    def add_process(self, pid: int, arrival_time: int, burst_time: int, priority: int = 0):
        """Menambahkan proses baru ke dalam scheduler"""
        process = Process(pid, arrival_time, burst_time, priority)
        self.processes.append(process)
    
    def reset_processes(self):
        """Reset semua proses ke kondisi awal"""
        for process in self.processes:
            process.remaining_time = process.burst_time
            process.remaining = process.burst_time
            process.completion_time = 0
            process.turnaround_time = 0
            process.waiting_time = 0
            process.response_time = -1
            process.start_time = -1
    
    def _calculate_times(self, processes: List[Process]) -> List[Process]:
        """Menghitung waktu turnaround, waiting, dan response untuk semua proses"""
        for process in processes:
            process.turnaround_time = process.completion_time - process.arrival_time
            process.waiting_time = process.turnaround_time - process.burst_time
            if process.response_time == -1:
                process.response_time = process.start_time - process.arrival_time
        return processes
    
    def fcfs_scheduling(self) -> Dict:
        """First Come First Served Scheduling - Fixed Implementation"""
        self.reset_processes()
        processes = deepcopy(self.processes)
        processes.sort(key=lambda p: p.arrival_time)
        
        current_time = 0
        gantt = []
        
        for process in processes:
            # Jika CPU idle, loncat ke waktu kedatangan proses
            if current_time < process.arrival_time:
                current_time = process.arrival_time
            
            process.start_time = current_time
            process.response_time = current_time - process.arrival_time
            
            gantt.append({
                'pid': process.pid,
                'start': current_time,
                'duration': process.burst_time
            })
            
            current_time += process.burst_time
            process.completion_time = current_time
        
        # Hitung times
        processes = self._calculate_times(processes)
        return self._calculate_metrics(processes, "FCFS", gantt)
    
    def sjf_scheduling(self) -> Dict:
        """Shortest Job First (Non-preemptive) Scheduling - Fixed Implementation"""
        self.reset_processes()
        processes = deepcopy(self.processes)
        processes.sort(key=lambda p: (p.arrival_time, p.burst_time))
        
        completed = 0
        current_time = 0
        ready_queue = []
        n = len(processes)
        idx = 0
        result = []
        gantt = []

        while completed < n:
            # Tambahkan proses yang sudah tiba ke ready queue
            while idx < n and processes[idx].arrival_time <= current_time:
                ready_queue.append(processes[idx])
                idx += 1
            
            if ready_queue:
                # Pilih proses dengan burst time terpendek
                ready_queue.sort(key=lambda p: (p.burst_time, p.pid))
                selected_process = ready_queue.pop(0)
                
                selected_process.start_time = current_time
                gantt.append({
                    'pid': selected_process.pid,
                    'start': current_time,
                    'duration': selected_process.burst_time
                })
                
                current_time += selected_process.burst_time
                selected_process.completion_time = current_time
                result.append(selected_process)
                completed += 1
            else:
                # CPU idle, loncat ke waktu kedatangan proses berikutnya
                if idx < n:
                    current_time = processes[idx].arrival_time
        
        # Hitung times
        result = self._calculate_times(result)
        return self._calculate_metrics(result, "SJF", gantt)
    
    def round_robin_scheduling(self, quantum: int = 2) -> Dict:
        """Round Robin Scheduling - Fixed Implementation"""
        self.reset_processes()
        processes = deepcopy(self.processes)
        
        queue = []
        time = 0
        n = len(processes)
        completed = 0
        idx = 0
        result = []
        visited = [False] * n
        gantt = []

        # Sort processes by arrival time for proper processing
        processes.sort(key=lambda p: p.arrival_time)

        while completed < n:
            # Add newly arrived processes to queue
            while idx < n and processes[idx].arrival_time <= time:
                if not visited[idx]:
                    queue.append(processes[idx])
                    visited[idx] = True
                idx += 1

            if queue:
                current_process = queue.pop(0)
                
                # Set start time and response time for first execution
                if current_process.start_time == -1:
                    current_process.start_time = time
                
                # Execute for quantum time or remaining time
                exec_time = min(quantum, current_process.remaining_time)
                gantt.append({
                    'pid': current_process.pid,
                    'start': time,
                    'duration': exec_time
                })
                
                time += exec_time
                current_process.remaining_time -= exec_time
                
                # Add newly arrived processes after execution
                while idx < n and processes[idx].arrival_time <= time:
                    if not visited[idx]:
                        queue.append(processes[idx])
                        visited[idx] = True
                    idx += 1
                
                # Check if process is completed
                if current_process.remaining_time > 0:
                    queue.append(current_process)  # Put back in queue
                else:
                    current_process.completion_time = time
                    result.append(current_process)
                    completed += 1
            else:
                # CPU idle, advance time
                time += 1
        
        # Hitung times
        result = self._calculate_times(result)
        return self._calculate_metrics(result, f"Round Robin (Quantum={quantum})", gantt)
    
    def priority_scheduling(self) -> Dict:
        """Priority Scheduling (Non-preemptive) - Fixed Implementation"""
        self.reset_processes()
        processes = deepcopy(self.processes)
        processes.sort(key=lambda p: (p.arrival_time, p.priority))
        
        completed = 0
        current_time = 0
        ready_queue = []
        idx = 0
        result = []
        n = len(processes)
        gantt = []

        while completed < n:
            # Tambahkan proses yang sudah tiba ke ready queue
            while idx < n and processes[idx].arrival_time <= current_time:
                ready_queue.append(processes[idx])
                idx += 1
            
            if ready_queue:
                # Pilih proses dengan prioritas tertinggi (nilai terkecil)
                ready_queue.sort(key=lambda p: (p.priority, p.pid))
                selected_process = ready_queue.pop(0)
                
                selected_process.start_time = current_time
                gantt.append({
                    'pid': selected_process.pid,
                    'start': current_time,
                    'duration': selected_process.burst_time
                })
                
                current_time += selected_process.burst_time
                selected_process.completion_time = current_time
                result.append(selected_process)
                completed += 1
            else:
                # CPU idle, loncat ke waktu kedatangan proses berikutnya
                if idx < n:
                    current_time = processes[idx].arrival_time
        
        # Hitung times
        result = self._calculate_times(result)
        return self._calculate_metrics(result, "Priority Scheduling", gantt)
    
    def _calculate_metrics(self, processes: List[Process], algorithm_name: str, gantt: List[Dict]) -> Dict:
        """Menghitung metrik kinerja"""
        if not processes:
            return {
                'algorithm': algorithm_name,
                'processes': [],
                'avg_waiting_time': 0,
                'avg_turnaround_time': 0,
                'avg_response_time': 0,
                'throughput': 0,
                'total_time': 0,
                'gantt': []
            }
        
        total_waiting_time = sum(p.waiting_time for p in processes)
        total_turnaround_time = sum(p.turnaround_time for p in processes)
        total_response_time = sum(p.response_time for p in processes)
        
        avg_waiting_time = total_waiting_time / len(processes)
        avg_turnaround_time = total_turnaround_time / len(processes)
        avg_response_time = total_response_time / len(processes)
        
        # Throughput = jumlah proses / total waktu eksekusi
        total_time = max(p.completion_time for p in processes)
        min_arrival = min(p.arrival_time for p in processes)
        throughput = len(processes) / (total_time - min_arrival) if (total_time - min_arrival) > 0 else 0
        
        return {
            'algorithm': algorithm_name,
            'processes': processes,
            'avg_waiting_time': avg_waiting_time,
            'avg_turnaround_time': avg_turnaround_time,
            'avg_response_time': avg_response_time,
            'throughput': throughput,
            'total_time': total_time,
            'gantt': gantt
        }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/input')
def input_page():
    return render_template('input_processes.html')

@app.route('/simulate', methods=['POST'])
def simulate():
    data = request.json
    processes = data.get('processes', [])
    quantum = data.get('quantum', 2)
    
    # Create scheduler and add processes
    scheduler = CPUScheduler()
    for i, process in enumerate(processes):
        scheduler.add_process(
            i + 1,
            int(process['arrival_time']),
            int(process['burst_time']),
            int(process['priority'])
        )
    
    # Run all algorithms
    results = {}
    
    # FCFS
    results['FCFS'] = scheduler.fcfs_scheduling()
    
    # SJF
    results['SJF'] = scheduler.sjf_scheduling()
    
    # Round Robin
    results['RR'] = scheduler.round_robin_scheduling(int(quantum))
    
    # Priority
    results['Priority'] = scheduler.priority_scheduling()
    
    # Convert results to JSON-serializable format
    json_results = {}
    gantt_data = {}
    
    for algo, result in results.items():
        json_results[algo] = {
            'algorithm': result['algorithm'],
            'avg_waiting_time': round(result['avg_waiting_time'], 2),
            'avg_turnaround_time': round(result['avg_turnaround_time'], 2),
            'avg_response_time': round(result['avg_response_time'], 2),
            'throughput': round(result['throughput'], 4),
            'total_time': result['total_time'],
            'processes': []
        }
        
        gantt_data[algo] = result['gantt']
        
        for process in result['processes']:
            json_results[algo]['processes'].append({
                'pid': process.pid,
                'arrival_time': process.arrival_time,
                'burst_time': process.burst_time,
                'priority': process.priority,
                'start_time': process.start_time,
                'completion_time': process.completion_time,
                'turnaround_time': process.turnaround_time,
                'waiting_time': process.waiting_time,
                'response_time': process.response_time
            })
    
    # Generate Gantt chart
    gantt_chart = generate_gantt_chart(gantt_data, json_results)
    
    return jsonify({
        'results': json_results,
        'gantt_chart': gantt_chart
    })

def generate_gantt_chart(gantt_data, results):
    """Generate Gantt chart visualization"""
    fig, axes = plt.subplots(2, 2, figsize=(18, 14))
    fig.suptitle('CPU Scheduling Algorithms - Gantt Charts', fontsize=20, fontweight='bold', y=0.95)
    
    algorithms = ['FCFS', 'SJF', 'RR', 'Priority']
    positions = [(0, 0), (0, 1), (1, 0), (1, 1)]
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD', '#98D8C8', '#F7DC6F']
    
    # Calculate global max time for consistent scaling
    max_time = 0
    for algo in algorithms:
        if algo in gantt_data and gantt_data[algo]:
            timeline_max = max(segment['start'] + segment['duration'] for segment in gantt_data[algo])
            max_time = max(max_time, timeline_max)
    
    for i, algo in enumerate(algorithms):
        if algo in gantt_data and gantt_data[algo]:
            ax = axes[positions[i][0]][positions[i][1]]
            gantt = gantt_data[algo]
            
            # Plot Gantt chart segments
            for segment in gantt:
                color = colors[(segment['pid'] - 1) % len(colors)]
                
                # Draw the main bar
                ax.barh(0, segment['duration'], left=segment['start'], 
                       color=color, alpha=0.8, edgecolor='black', linewidth=1.5, height=0.6)
                
                # Add process label
                ax.text(segment['start'] + segment['duration']/2, 0, 
                       f"P{segment['pid']}", ha='center', va='center', 
                       fontweight='bold', fontsize=11, color='white')
            
            # Add time labels
            time_points = set()
            for segment in gantt:
                time_points.add(segment['start'])
                time_points.add(segment['start'] + segment['duration'])
            
            for time_point in sorted(time_points):
                ax.text(time_point, -0.5, str(time_point), 
                       ha='center', va='top', fontsize=9, fontweight='bold')
            
            # Customize the subplot
            ax.set_title(f'{results[algo]["algorithm"]}', fontweight='bold', fontsize=14, pad=20)
            ax.set_xlabel('Time Units', fontsize=12, fontweight='bold')
            ax.set_ylabel('CPU', fontsize=12, fontweight='bold')
            ax.set_ylim(-0.8, 0.8)
            ax.set_xlim(-0.5, max_time + 0.5)
            
            # Add grid
            ax.grid(True, alpha=0.3, axis='x', linestyle='--')
            ax.set_yticks([])
            
            # Add performance metrics as text
            metrics_text = f'Avg WT: {results[algo]["avg_waiting_time"]:.2f} | Avg TAT: {results[algo]["avg_turnaround_time"]:.2f}'
            ax.text(0.02, 0.95, metrics_text, transform=ax.transAxes, 
                   bbox=dict(boxstyle="round,pad=0.3", facecolor="lightblue", alpha=0.7),
                   fontsize=10, verticalalignment='top')
            
            # Set consistent x-axis ticks
            if max_time > 0:
                tick_interval = max(1, max_time // 10)
                ax.set_xticks(range(0, max_time + 1, tick_interval))
    
    # Add a legend
    legend_elements = [plt.Rectangle((0,0),1,1, facecolor=colors[i % len(colors)], 
                                   edgecolor='black', alpha=0.8, 
                                   label=f'Process {i+1}') for i in range(5)]
    fig.legend(handles=legend_elements, loc='upper center', bbox_to_anchor=(0.5, 0.02), 
              ncol=5, fontsize=12, frameon=True, fancybox=True, shadow=True)
    
    plt.tight_layout()
    plt.subplots_adjust(top=0.9, bottom=0.1)
    
    # Convert plot to base64 string
    img = io.BytesIO()
    plt.savefig(img, format='png', dpi=200, bbox_inches='tight', facecolor='white')
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode()
    plt.close()
    
    return plot_url

@app.route('/results')
def results_page():
    return render_template('results.html')

if __name__ == '__main__':
    app.run(debug=True)