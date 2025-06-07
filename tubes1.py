import time
from typing import List, Dict, Tuple
import matplotlib.pyplot as plt
import pandas as pd

class Process:
    def __init__(self, pid: int, arrival_time: int, burst_time: int, priority: int = 0):
        self.pid = pid
        self.arrival_time = arrival_time
        self.burst_time = burst_time
        self.priority = priority
        self.remaining_time = burst_time
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
        self.results = {}
    
    def add_process(self, pid: int, arrival_time: int, burst_time: int, priority: int = 0):
        """Menambahkan proses baru ke dalam scheduler"""
        process = Process(pid, arrival_time, burst_time, priority)
        self.processes.append(process)
    
    def reset_processes(self):
        """Reset semua proses ke kondisi awal"""
        for process in self.processes:
            process.remaining_time = process.burst_time
            process.completion_time = 0
            process.turnaround_time = 0
            process.waiting_time = 0
            process.response_time = -1
            process.start_time = -1
    
    def fcfs_scheduling(self) -> Dict:
        """First Come First Served Scheduling"""
        self.reset_processes()
        processes = sorted(self.processes, key=lambda x: x.arrival_time)
        current_time = 0
        
        for process in processes:
            if current_time < process.arrival_time:
                current_time = process.arrival_time
            
            process.start_time = current_time
            process.response_time = current_time - process.arrival_time
            current_time += process.burst_time
            process.completion_time = current_time
            process.turnaround_time = process.completion_time - process.arrival_time
            process.waiting_time = process.turnaround_time - process.burst_time
        
        return self._calculate_metrics(processes, "FCFS")
    
    def sjf_scheduling(self) -> Dict:
        """Shortest Job First (Non-preemptive) Scheduling"""
        self.reset_processes()
        processes = self.processes.copy()
        completed = []
        current_time = 0
        
        while processes:
            # Cari proses yang sudah tiba
            available = [p for p in processes if p.arrival_time <= current_time]
            
            if not available:
                current_time = min(p.arrival_time for p in processes)
                continue
            
            # Pilih proses dengan burst time terpendek
            shortest = min(available, key=lambda x: x.burst_time)
            processes.remove(shortest)
            
            shortest.start_time = current_time
            shortest.response_time = current_time - shortest.arrival_time
            current_time += shortest.burst_time
            shortest.completion_time = current_time
            shortest.turnaround_time = shortest.completion_time - shortest.arrival_time
            shortest.waiting_time = shortest.turnaround_time - shortest.burst_time
            
            completed.append(shortest)
        
        return self._calculate_metrics(completed, "SJF")
    
    def round_robin_scheduling(self, quantum: int = 2) -> Dict:
        """Round Robin Scheduling"""
        self.reset_processes()
        processes = self.processes.copy()
        ready_queue = []
        current_time = 0
        completed = []
        
        # Sort by arrival time
        processes.sort(key=lambda x: x.arrival_time)
        
        while processes or ready_queue:
            # Add arrived processes to ready queue
            while processes and processes[0].arrival_time <= current_time:
                ready_queue.append(processes.pop(0))
            
            if not ready_queue:
                current_time = processes[0].arrival_time if processes else current_time
                continue
            
            current_process = ready_queue.pop(0)
            
            # Set response time if first execution
            if current_process.response_time == -1:
                current_process.response_time = current_time - current_process.arrival_time
                current_process.start_time = current_time
            
            # Execute for quantum time or remaining time
            execution_time = min(quantum, current_process.remaining_time)
            current_time += execution_time
            current_process.remaining_time -= execution_time
            
            # Add newly arrived processes
            while processes and processes[0].arrival_time <= current_time:
                ready_queue.append(processes.pop(0))
            
            if current_process.remaining_time > 0:
                ready_queue.append(current_process)
            else:
                current_process.completion_time = current_time
                current_process.turnaround_time = current_process.completion_time - current_process.arrival_time
                current_process.waiting_time = current_process.turnaround_time - current_process.burst_time
                completed.append(current_process)
        
        return self._calculate_metrics(completed, f"Round Robin (Quantum={quantum})")
    
    def priority_scheduling(self) -> Dict:
        """Priority Scheduling (Non-preemptive, lower number = higher priority)"""
        self.reset_processes()
        processes = self.processes.copy()
        completed = []
        current_time = 0
        
        while processes:
            # Cari proses yang sudah tiba
            available = [p for p in processes if p.arrival_time <= current_time]
            
            if not available:
                current_time = min(p.arrival_time for p in processes)
                continue
            
            # Pilih proses dengan prioritas tertinggi (nilai terkecil)
            highest_priority = min(available, key=lambda x: x.priority)
            processes.remove(highest_priority)
            
            highest_priority.start_time = current_time
            highest_priority.response_time = current_time - highest_priority.arrival_time
            current_time += highest_priority.burst_time
            highest_priority.completion_time = current_time
            highest_priority.turnaround_time = highest_priority.completion_time - highest_priority.arrival_time
            highest_priority.waiting_time = highest_priority.turnaround_time - highest_priority.burst_time
            
            completed.append(highest_priority)
        
        return self._calculate_metrics(completed, "Priority Scheduling")
    
    def _calculate_metrics(self, processes: List[Process], algorithm_name: str) -> Dict:
        """Menghitung metrik kinerja"""
        total_waiting_time = sum(p.waiting_time for p in processes)
        total_turnaround_time = sum(p.turnaround_time for p in processes)
        total_response_time = sum(p.response_time for p in processes)
        
        avg_waiting_time = total_waiting_time / len(processes)
        avg_turnaround_time = total_turnaround_time / len(processes)
        avg_response_time = total_response_time / len(processes)
        
        # Throughput = jumlah proses / total waktu eksekusi
        total_time = max(p.completion_time for p in processes)
        throughput = len(processes) / total_time if total_time > 0 else 0
        
        return {
            'algorithm': algorithm_name,
            'processes': processes,
            'avg_waiting_time': avg_waiting_time,
            'avg_turnaround_time': avg_turnaround_time,
            'avg_response_time': avg_response_time,
            'throughput': throughput,
            'total_time': total_time
        }
    
    def run_all_algorithms(self, quantum: int = 2) -> Dict:
        """Menjalankan semua algoritma dan membandingkan hasilnya"""
        results = {}
        
        print("=" * 80)
        print("CPU SCHEDULING ALGORITHMS SIMULATION")
        print("=" * 80)
        
        # FCFS
        print("\n1. FIRST COME FIRST SERVED (FCFS)")
        print("-" * 50)
        results['FCFS'] = self.fcfs_scheduling()
        self._print_results(results['FCFS'])
        
        # SJF
        print("\n2. SHORTEST JOB FIRST (SJF)")
        print("-" * 50)
        results['SJF'] = self.sjf_scheduling()
        self._print_results(results['SJF'])
        
        # Round Robin
        print(f"\n3. ROUND ROBIN (Quantum = {quantum})")
        print("-" * 50)
        results['RR'] = self.round_robin_scheduling(quantum)
        self._print_results(results['RR'])
        
        # Priority
        print("\n4. PRIORITY SCHEDULING")
        print("-" * 50)
        results['Priority'] = self.priority_scheduling()
        self._print_results(results['Priority'])
        
        # Comparison
        print("\n" + "=" * 80)
        print("PERFORMANCE COMPARISON")
        print("=" * 80)
        self._compare_algorithms(results)
        
        return results
    
    def _print_results(self, result: Dict):
        """Mencetak hasil scheduling algorithm"""
        print(f"\nAlgorithm: {result['algorithm']}")
        print(f"{'PID':<5} {'AT':<5} {'BT':<5} {'Priority':<8} {'ST':<5} {'CT':<5} {'TAT':<5} {'WT':<5} {'RT':<5}")
        print("-" * 60)
        
        for process in sorted(result['processes'], key=lambda x: x.pid):
            print(f"{process.pid:<5} {process.arrival_time:<5} {process.burst_time:<5} "
                  f"{process.priority:<8} {process.start_time:<5} {process.completion_time:<5} "
                  f"{process.turnaround_time:<5} {process.waiting_time:<5} {process.response_time:<5}")
        
        print(f"\nAverage Waiting Time: {result['avg_waiting_time']:.2f}")
        print(f"Average Turnaround Time: {result['avg_turnaround_time']:.2f}")
        print(f"Average Response Time: {result['avg_response_time']:.2f}")
        print(f"Throughput: {result['throughput']:.4f} processes/unit time")
        print(f"Total Execution Time: {result['total_time']}")
    
    def _compare_algorithms(self, results: Dict):
        """Membandingkan performa semua algoritma"""
        comparison_data = []
        
        for algo_name, result in results.items():
            comparison_data.append({
                'Algorithm': result['algorithm'],
                'Avg Waiting Time': f"{result['avg_waiting_time']:.2f}",
                'Avg Turnaround Time': f"{result['avg_turnaround_time']:.2f}",
                'Avg Response Time': f"{result['avg_response_time']:.2f}",
                'Throughput': f"{result['throughput']:.4f}",
                'Total Time': result['total_time']
            })
        
        df = pd.DataFrame(comparison_data)
        print(df.to_string(index=False))
        
        # Find best performing algorithm for each metric
        print(f"\n{'BEST PERFORMANCE ANALYSIS'}")
        print("-" * 40)
        
        best_waiting = min(results.items(), key=lambda x: x[1]['avg_waiting_time'])
        best_turnaround = min(results.items(), key=lambda x: x[1]['avg_turnaround_time'])
        best_response = min(results.items(), key=lambda x: x[1]['avg_response_time'])
        best_throughput = max(results.items(), key=lambda x: x[1]['throughput'])
        
        print(f"Best Average Waiting Time: {best_waiting[1]['algorithm']} ({best_waiting[1]['avg_waiting_time']:.2f})")
        print(f"Best Average Turnaround Time: {best_turnaround[1]['algorithm']} ({best_turnaround[1]['avg_turnaround_time']:.2f})")
        print(f"Best Average Response Time: {best_response[1]['algorithm']} ({best_response[1]['avg_response_time']:.2f})")
        print(f"Best Throughput: {best_throughput[1]['algorithm']} ({best_throughput[1]['throughput']:.4f})")
    
    def create_gantt_chart(self, results: Dict):
        """Membuat Gantt chart untuk visualisasi"""
        try:
            fig, axes = plt.subplots(2, 2, figsize=(15, 10))
            fig.suptitle('CPU Scheduling Algorithms - Gantt Charts', fontsize=16)
            
            algorithms = ['FCFS', 'SJF', 'RR', 'Priority']
            positions = [(0, 0), (0, 1), (1, 0), (1, 1)]
            
            for i, algo in enumerate(algorithms):
                if algo in results:
                    ax = axes[positions[i][0]][positions[i][1]]
                    processes = sorted(results[algo]['processes'], key=lambda x: x.start_time)
                    
                    colors = plt.cm.Set3(range(len(processes)))
                    
                    for j, process in enumerate(processes):
                        ax.barh(f'P{process.pid}', process.burst_time, 
                               left=process.start_time, color=colors[j], 
                               alpha=0.8, edgecolor='black')
                        ax.text(process.start_time + process.burst_time/2, j, 
                               f'P{process.pid}', ha='center', va='center', fontweight='bold')
                    
                    ax.set_title(f'{results[algo]["algorithm"]}')
                    ax.set_xlabel('Time')
                    ax.set_ylabel('Process')
                    ax.grid(True, alpha=0.3)
            
            plt.tight_layout()
            plt.show()
        except ImportError:
            print("Matplotlib tidak tersedia. Gantt chart tidak dapat ditampilkan.")

def get_user_input():
    """Mengambil input dari pengguna"""
    print("CPU SCHEDULING SIMULATOR")
    print("=" * 40)
    
    num_processes = int(input("Masukkan jumlah proses: "))
    scheduler = CPUScheduler()
    
    print("\nMasukkan data untuk setiap proses:")
    for i in range(num_processes):
        print(f"\nProses {i+1}:")
        arrival_time = int(input(f"  Waktu kedatangan (Arrival Time): "))
        burst_time = int(input(f"  Waktu eksekusi (Burst Time): "))
        priority = int(input(f"  Prioritas (angka kecil = prioritas tinggi): "))
        
        scheduler.add_process(i+1, arrival_time, burst_time, priority)
    
    quantum = int(input("\nMasukkan quantum untuk Round Robin: "))
    
    return scheduler, quantum

def main():
    """Fungsi utama program"""
    # Pilihan: input manual atau contoh data
    choice = input("Pilih mode:\n1. Input manual\n2. Gunakan data contoh\nPilihan (1/2): ")
    
    if choice == "1":
        scheduler, quantum = get_user_input()
    else:
        # Data contoh untuk demonstrasi
        scheduler = CPUScheduler()
        # Proses dengan karakteristik yang berbeda untuk menunjukkan perbedaan algoritma
        scheduler.add_process(1, 0, 8, 3)   # P1: AT=0, BT=8, Priority=3
        scheduler.add_process(2, 1, 4, 1)   # P2: AT=1, BT=4, Priority=1 (highest)
        scheduler.add_process(3, 2, 9, 4)   # P3: AT=2, BT=9, Priority=4
        scheduler.add_process(4, 3, 5, 2)   # P4: AT=3, BT=5, Priority=2
        scheduler.add_process(5, 4, 2, 5)   # P5: AT=4, BT=2, Priority=5 (lowest)
        quantum = 3
        
        print("Menggunakan data contoh:")
        print("P1: AT=0, BT=8, Priority=3")
        print("P2: AT=1, BT=4, Priority=1")
        print("P3: AT=2, BT=9, Priority=4")
        print("P4: AT=3, BT=5, Priority=2")
        print("P5: AT=4, BT=2, Priority=5")
        print(f"Quantum = {quantum}")
    
    # Jalankan simulasi
    results = scheduler.run_all_algorithms(quantum)
    
    # Analisis mendalam
    print("\n" + "=" * 80)
    print("ANALISIS MENDALAM ALGORITMA CPU SCHEDULING")
    print("=" * 80)
    
    analyze_algorithms(results)
    
    # Buat gantt chart jika matplotlib tersedia
    try:
        scheduler.create_gantt_chart(results)
    except:
        pass

def analyze_algorithms(results: Dict):
    """Analisis mendalam tentang kelebihan dan kekurangan setiap algoritma"""
    
    # print("\n1. FIRST COME FIRST SERVED (FCFS)")
    # print("-" * 50)
    # print("KELEBIHAN:")
    # print("• Sederhana dan mudah diimplementasikan")
    # print("• Fair - tidak ada starvation")
    # print("• Overhead rendah")
    # print("• Cocok untuk batch processing")
    
    # print("\nKEKURANGAN:")
    # print("• Convoy effect - proses pendek menunggu proses panjang")
    # print("• Waiting time tinggi untuk proses yang datang belakangan")
    # print("• Tidak optimal untuk sistem interaktif")
    # print(f"• Pada simulasi ini: Avg WT = {results['FCFS']['avg_waiting_time']:.2f}")
    
    # print("\n2. SHORTEST JOB FIRST (SJF)")
    # print("-" * 50)
    # print("KELEBIHAN:")
    # print("• Optimal untuk meminimalkan average waiting time")
    # print("• Throughput tinggi untuk proses-proses pendek")
    # print("• Efisien untuk batch systems")
    # print(f"• Pada simulasi ini: Avg WT = {results['SJF']['avg_waiting_time']:.2f} (biasanya terbaik)")
    
    # print("\nKEKURANGAN:")
    # print("• Starvation - proses panjang bisa menunggu sangat lama")
    # print("• Sulit memprediksi burst time di dunia nyata")
    # print("• Tidak fair untuk proses dengan burst time panjang")
    # print("• Tidak cocok untuk sistem real-time")
    
    # print("\n3. ROUND ROBIN")
    # print("-" * 50)
    # print("KELEBIHAN:")
    # print("• Fair - setiap proses mendapat kesempatan yang sama")
    # print("• Responsif untuk proses interaktif")
    # print("• Mencegah starvation")
    # print("• Cocok untuk time-sharing systems")
    # print(f"• Response time yang baik: {results['RR']['avg_response_time']:.2f}")
    
    # print("\nKEKURANGAN:")
    # print("• Context switching overhead tinggi")
    # print("• Performa bergantung pada pemilihan quantum")
    # print("• Tidak optimal untuk proses dengan burst time sangat berbeda")
    # print(f"• Avg WT = {results['RR']['avg_waiting_time']:.2f}")
    
    # print("\n4. PRIORITY SCHEDULING")
    # print("-" * 50)
    # print("KELEBIHAN:")
    # print("• Fleksibel - dapat mengutamakan proses penting")
    # print("• Cocok untuk sistem dengan hierarki proses")
    # print("• Dapat disesuaikan dengan kebutuhan sistem")
    # print(f"• Pada simulasi ini: Avg WT = {results['Priority']['avg_waiting_time']:.2f}")
    
    # print("\nKEKURANGAN:")
    # print("• Starvation untuk proses dengan prioritas rendah")
    # print("• Kompleks dalam penentuan prioritas")
    # print("• Dapat menyebabkan priority inversion")
    # print("• Membutuhkan mekanisme aging untuk mencegah starvation")
    
    # # Rekomendasi penggunaan
    # print("\n" + "=" * 60)
    # print("REKOMENDASI PENGGUNAAN")
    # print("=" * 60)
    
    # print("\nFCFS cocok untuk:")
    # print("• Batch processing systems")
    # print("• Sistem dengan proses yang memiliki burst time serupa")
    # print("• Aplikasi yang mengutamakan kesederhanaan")
    
    # print("\nSJF cocok untuk:")
    # print("• Batch systems dengan informasi burst time yang akurat")
    # print("• Sistem yang mengutamakan throughput")
    # print("• Lingkungan dengan variasi burst time yang besar")
    
    # print("\nRound Robin cocok untuk:")
    # print("• Time-sharing systems")
    # print("• Interactive systems")
    # print("• Multi-user environments")
    # print("• Sistem yang mengutamakan responsiveness")
    
    # print("\nPriority Scheduling cocok untuk:")
    # print("• Real-time systems")
    # print("• Systems dengan proses critical dan non-critical")
    # print("• Embedded systems")
    # print("• Sistem yang membutuhkan kontrol granular")
    
    # Analisis berdasarkan hasil simulasi
    print(f"\n{'KESIMPULAN BERDASARKAN SIMULASI'}")
    print("-" * 50)
    
    best_wt = min(results.items(), key=lambda x: x[1]['avg_waiting_time'])
    best_rt = min(results.items(), key=lambda x: x[1]['avg_response_time'])
    best_throughput = max(results.items(), key=lambda x: x[1]['throughput'])
    
    # print(f"Untuk dataset ini:")
    # print(f"• {best_wt[1]['algorithm']} memberikan waiting time terbaik")
    # print(f"• {best_rt[1]['algorithm']} memberikan response time terbaik") 
    # print(f"• {best_throughput[1]['algorithm']} memberikan throughput terbaik")
    
    # print(f"\nPemilihan algoritma terbaik bergantung pada:")
    # print("• Karakteristik workload (burst time, arrival pattern)")
    # print("• Prioritas sistem (responsiveness vs throughput)")
    # print("• Overhead yang dapat ditoleransi")
    # print("• Requirement fairness dan starvation prevention")

if __name__ == "__main__":
    main()