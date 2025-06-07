from flask import Flask, render_template, request, jsonify
import json
import base64
import io
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from tubes1 import CPUScheduler, Process

app = Flask(__name__)

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
    
    # Run all algorithms and get execution timelines
    results = {}
    timelines = {}
    
    # FCFS
    results['FCFS'] = scheduler.fcfs_scheduling()
    timelines['FCFS'] = generate_fcfs_timeline(processes)
    
    # SJF
    results['SJF'] = scheduler.sjf_scheduling()
    timelines['SJF'] = generate_sjf_timeline(processes)
    
    # Round Robin
    results['RR'] = scheduler.round_robin_scheduling(int(quantum))
    timelines['RR'] = generate_rr_timeline(processes, int(quantum))
    
    # Priority
    results['Priority'] = scheduler.priority_scheduling()
    timelines['Priority'] = generate_priority_timeline(processes)
    
    # Convert results to JSON-serializable format
    json_results = {}
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
    
    # Generate improved Gantt chart
    gantt_chart = generate_improved_gantt_chart(timelines, json_results)
    
    return jsonify({
        'results': json_results,
        'gantt_chart': gantt_chart
    })

def generate_fcfs_timeline(processes):
    """Generate FCFS execution timeline"""
    timeline = []
    current_time = 0
    
    # Sort by arrival time
    sorted_processes = sorted(enumerate(processes, 1), key=lambda x: x[1]['arrival_time'])
    
    for pid, process in sorted_processes:
        start_time = max(current_time, process['arrival_time'])
        end_time = start_time + process['burst_time']
        
        timeline.append({
            'pid': pid,
            'start': start_time,
            'end': end_time,
            'duration': process['burst_time']
        })
        
        current_time = end_time
    
    return timeline

def generate_sjf_timeline(processes):
    """Generate SJF (Shortest Job First) execution timeline"""
    timeline = []
    current_time = 0
    remaining_processes = [(i+1, p.copy()) for i, p in enumerate(processes)]
    
    while remaining_processes:
        # Get available processes at current time
        available = [p for p in remaining_processes if p[1]['arrival_time'] <= current_time]
        
        if not available:
            # Jump to next arrival time
            current_time = min(p[1]['arrival_time'] for p in remaining_processes)
            continue
        
        # Select shortest job among available
        selected = min(available, key=lambda x: x[1]['burst_time'])
        pid, process = selected
        
        start_time = current_time
        end_time = start_time + process['burst_time']
        
        timeline.append({
            'pid': pid,
            'start': start_time,
            'end': end_time,
            'duration': process['burst_time']
        })
        
        current_time = end_time
        remaining_processes.remove(selected)
    
    return timeline

def generate_rr_timeline(processes, quantum):
    """Generate Round Robin execution timeline"""
    timeline = []
    current_time = 0
    queue = []
    remaining_processes = {i+1: p['burst_time'] for i, p in enumerate(processes)}
    arrival_times = {i+1: p['arrival_time'] for i, p in enumerate(processes)}
    
    # Add initially available processes to queue
    for pid in range(1, len(processes) + 1):
        if arrival_times[pid] <= current_time:
            queue.append(pid)
    
    while queue or any(remaining_processes[pid] > 0 for pid in remaining_processes):
        # Add newly arrived processes to queue
        for pid in range(1, len(processes) + 1):
            if (arrival_times[pid] <= current_time and 
                remaining_processes[pid] > 0 and 
                pid not in queue):
                queue.append(pid)
        
        if not queue:
            # Jump to next arrival time
            next_arrival = min(arrival_times[pid] for pid in remaining_processes 
                             if remaining_processes[pid] > 0 and arrival_times[pid] > current_time)
            current_time = next_arrival
            continue
        
        # Execute current process
        current_pid = queue.pop(0)
        execution_time = min(quantum, remaining_processes[current_pid])
        
        timeline.append({
            'pid': current_pid,
            'start': current_time,
            'end': current_time + execution_time,
            'duration': execution_time
        })
        
        current_time += execution_time
        remaining_processes[current_pid] -= execution_time
        
        # Add newly arrived processes
        for pid in range(1, len(processes) + 1):
            if (arrival_times[pid] <= current_time and 
                remaining_processes[pid] > 0 and 
                pid not in queue and pid != current_pid):
                queue.append(pid)
        
        # Add current process back to queue if not finished
        if remaining_processes[current_pid] > 0:
            queue.append(current_pid)
    
    return timeline

def generate_priority_timeline(processes):
    """Generate Priority scheduling execution timeline"""
    timeline = []
    current_time = 0
    remaining_processes = [(i+1, p.copy()) for i, p in enumerate(processes)]
    
    while remaining_processes:
        # Get available processes at current time
        available = [p for p in remaining_processes if p[1]['arrival_time'] <= current_time]
        
        if not available:
            # Jump to next arrival time
            current_time = min(p[1]['arrival_time'] for p in remaining_processes)
            continue
        
        # Select highest priority (lowest priority number) among available
        selected = min(available, key=lambda x: x[1]['priority'])
        pid, process = selected
        
        start_time = current_time
        end_time = start_time + process['burst_time']
        
        timeline.append({
            'pid': pid,
            'start': start_time,
            'end': end_time,
            'duration': process['burst_time']
        })
        
        current_time = end_time
        remaining_processes.remove(selected)
    
    return timeline

def generate_improved_gantt_chart(timelines, results):
    """Generate improved Gantt chart with accurate timelines"""
    fig, axes = plt.subplots(2, 2, figsize=(18, 14))
    fig.suptitle('CPU Scheduling Algorithms - Gantt Charts', fontsize=20, fontweight='bold', y=0.95)
    
    algorithms = ['FCFS', 'SJF', 'RR', 'Priority']
    positions = [(0, 0), (0, 1), (1, 0), (1, 1)]
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD', '#98D8C8', '#F7DC6F']
    
    # Calculate global max time for consistent scaling
    max_time = 0
    for algo in algorithms:
        if algo in timelines:
            timeline_max = max(segment['end'] for segment in timelines[algo])
            max_time = max(max_time, timeline_max)
    
    for i, algo in enumerate(algorithms):
        if algo in timelines:
            ax = axes[positions[i][0]][positions[i][1]]
            timeline = timelines[algo]
            
            # Plot Gantt chart segments
            for segment in timeline:
                color = colors[(segment['pid'] - 1) % len(colors)]
                
                # Draw the main bar
                ax.barh(0, segment['duration'], left=segment['start'], 
                       color=color, alpha=0.8, edgecolor='black', linewidth=1.5, height=0.6)
                
                # Add process label
                ax.text(segment['start'] + segment['duration']/2, 0, 
                       f"P{segment['pid']}", ha='center', va='center', 
                       fontweight='bold', fontsize=11, color='white')
                
                # Add time labels at the bottom
                if segment['start'] == 0 or not any(s['end'] == segment['start'] for s in timeline):
                    ax.text(segment['start'], -0.5, str(segment['start']), 
                           ha='center', va='top', fontsize=9, fontweight='bold')
                
                ax.text(segment['end'], -0.5, str(segment['end']), 
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