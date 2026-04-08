import socket
import threading
import time
import queue
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

# Common services
COMMON_PORTS = {
    21: 'FTP', 22: 'SSH', 80: 'HTTP', 443: 'HTTPS'
}

class PortScanner:
    def __init__(self, target, start_port, end_port):
        self.target = target
        self.start_port = start_port
        self.end_port = end_port
        self.queue = queue.Queue()
        self.stop_flag = False

    def scan_port(self, port):
        if self.stop_flag:
            return
        try:
            s = socket.socket()
            s.settimeout(0.5)
            result = s.connect_ex((self.target, port))

            if result == 0:
                service = COMMON_PORTS.get(port, "Unknown")
                self.queue.put(("open", port, service))
            else:
                self.queue.put(("closed", port, "Closed"))

            s.close()

        except:
            pass

    def start(self):
        for port in range(self.start_port, self.end_port + 1):
            if self.stop_flag:
                break
            threading.Thread(target=self.scan_port, args=(port,)).start()

        time.sleep(1)
        self.queue.put(("done", None, None))

    def stop(self):
        self.stop_flag = True


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Smart Port Scanner")
        self.geometry("650x500")

        self.scanner = None

        self.create_ui()

    def create_ui(self):
        frame = ttk.Frame(self)
        frame.pack(pady=10)

        ttk.Label(frame, text="Target IP").grid(row=0, column=0)
        self.target = ttk.Entry(frame)
        self.target.grid(row=0, column=1)

        ttk.Label(frame, text="Start Port").grid(row=1, column=0)
        self.start_port = ttk.Entry(frame)
        self.start_port.insert(0, "1")
        self.start_port.grid(row=1, column=1)

        ttk.Label(frame, text="End Port").grid(row=2, column=0)
        self.end_port = ttk.Entry(frame)
        self.end_port.insert(0, "100")
        self.end_port.grid(row=2, column=1)

        ttk.Button(frame, text="Start Scan", command=self.start_scan).grid(row=3, column=0, pady=5)
        ttk.Button(frame, text="Stop", command=self.stop_scan).grid(row=3, column=1, pady=5)

        self.text = tk.Text(self, height=22)
        self.text.pack(fill="both", expand=True)

        ttk.Button(self, text="Save Results", command=self.save_results).pack(pady=5)

    def start_scan(self):
        try:
            target = socket.gethostbyname(self.target.get())
            start = int(self.start_port.get())
            end = int(self.end_port.get())
        except:
            messagebox.showerror("Error", "Invalid input")
            return

        self.text.delete("1.0", tk.END)

        self.scanner = PortScanner(target, start, end)
        threading.Thread(target=self.scanner.start).start()

        self.update_ui()

    def stop_scan(self):
        if self.scanner:
            self.scanner.stop()

    def update_ui(self):
        if not self.scanner:
            return

        try:
            while True:
                msg = self.scanner.queue.get_nowait()

                if msg[0] == "open":
                    self.text.insert(tk.END, f"[OPEN] Port {msg[1]} ({msg[2]})\n")

                elif msg[0] == "closed":
                    # Limit closed ports display to avoid flooding
                    if msg[1] <= 50:
                        self.text.insert(tk.END, f"[CLOSED] Port {msg[1]}\n")

                elif msg[0] == "done":
                    self.text.insert(tk.END, "\nScan Completed\n")
                    return

        except queue.Empty:
            pass

        self.after(100, self.update_ui)

    def save_results(self):
        data = self.text.get("1.0", tk.END)
        file = filedialog.asksaveasfilename(defaultextension=".txt")
        if file:
            with open(file, "w") as f:
                f.write(data)


if __name__ == "__main__":
    app = App()
    app.mainloop()
