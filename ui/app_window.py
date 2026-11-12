"""
Desktop GUI Application for SmartMart Retail Group.
Built with Tkinter and Matplotlib. Implements IPipelineObserver for non-blocking asynchronous updates.
"""
import os
import sys
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Dict, Any, Optional

import matplotlib
matplotlib.use('TkAgg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from models.faulty_record import FaultyRecord
from models.analytics_result import AnalyticsResult
from facade.pipeline_observer_interface import IPipelineObserver
from facade.analytics_pipeline_facade import AnalyticsPipelineFacade
from export.report_exporter import ReportExporter


class SmartMartApp(tk.Tk, IPipelineObserver):

    DEFAULT_DATASET_PATHS = [
        r"C:\Users\Kavijan Kavi\Desktop\4Th semester final assignment\APDP Final Assignment\smartretail_transactions(in).csv",
        r"C:\Users\Kavijan Kavi\Desktop\4Th Semester Briefs\smartretail_transactions(in).csv",
        "smartretail_transactions_combined.csv"
    ]

    def __init__(self):
        super().__init__()
        self.title("SmartMart Retail Group - Operational Data Processing & Analytics Platform")
        self.geometry("1280x820")
        self.minsize(1050, 700)

        # Style configuration
        self.style = ttk.Style(self)
        try:
            self.style.theme_use('clam')
        except Exception:
            pass
        self._configure_styles()

        # Backend Facade
        self.facade = AnalyticsPipelineFacade()
        self.facade.register_observer(self)

        # State
        self.current_results: Optional[Dict[str, AnalyticsResult]] = None
        self.is_processing: bool = False

        # Build Interface
        self._build_layout()
        self._auto_detect_dataset()

    def _configure_styles(self):
        self.style.configure('.', font=('Segoe UI', 10))
        self.style.configure('Header.TLabel', font=('Segoe UI', 15, 'bold'), foreground='#1e3a8a')
        self.style.configure('SubHeader.TLabel', font=('Segoe UI', 11, 'bold'), foreground='#334155')
        self.style.configure('MetricCard.TFrame', background='#ffffff', relief='ridge')
        self.style.configure('Accent.TButton', font=('Segoe UI', 10, 'bold'), background='#2563eb', foreground='#ffffff')

    def _auto_detect_dataset(self):
        for p in self.DEFAULT_DATASET_PATHS:
            if os.path.exists(p):
                self.file_path_var.set(p)
                self.status_var.set(f"Default dataset auto-detected: {os.path.basename(p)} ({os.path.getsize(p)/(1024*1024):.1f} MB)")
                return
        self.status_var.set("Ready. Please select a retail transaction dataset.")

    def _build_layout(self):
        # Top Header Bar
        header_frame = ttk.Frame(self, padding="15 10 15 10")
        header_frame.pack(fill=tk.X)

        title_lbl = ttk.Label(header_frame, text="SmartMart Retail Analytics Platform", style='Header.TLabel')
        title_lbl.pack(side=tk.LEFT)

        subtitle_lbl = ttk.Label(header_frame, text="  |  Large-Scale Chunk Processing & Decision Support Engine", font=('Segoe UI', 10))
        subtitle_lbl.pack(side=tk.LEFT, pady=3)

        # Main Tabbed Notebook
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Tabs
        self.tab_dashboard = ttk.Frame(self.notebook, padding=10)
        self.tab_peak_sales = ttk.Frame(self.notebook, padding=10)
        self.tab_segmentation = ttk.Frame(self.notebook, padding=10)
        self.tab_seasonal = ttk.Frame(self.notebook, padding=10)
        self.tab_revenue = ttk.Frame(self.notebook, padding=10)
        self.tab_anomalies = ttk.Frame(self.notebook, padding=10)
        self.tab_regional = ttk.Frame(self.notebook, padding=10)
        self.tab_dlq = ttk.Frame(self.notebook, padding=10)

        self.notebook.add(self.tab_dashboard, text=" 📊 Pipeline Dashboard ")
        self.notebook.add(self.tab_peak_sales, text=" ⏰ Peak Sales ")
        self.notebook.add(self.tab_segmentation, text=" 👥 Customer Segmentation ")
        self.notebook.add(self.tab_seasonal, text=" 📈 Seasonal & Promo ")
        self.notebook.add(self.tab_revenue, text=" 💰 Revenue & Products ")
        self.notebook.add(self.tab_anomalies, text=" ⚠️ Anomaly Detection ")
        self.notebook.add(self.tab_regional, text=" 🏬 Store & Regional ")
        self.notebook.add(self.tab_dlq, text=" 🛡️ Dead-Letter Queue (DLQ) ")

        # Build each tab view
        self._build_dashboard_tab()
        self._build_peak_sales_tab()
        self._build_segmentation_tab()
        self._build_seasonal_tab()
        self._build_revenue_tab()
        self._build_anomalies_tab()
        self._build_regional_tab()
        self._build_dlq_tab()

        # Bottom Status Bar
        status_bar = ttk.Frame(self, relief=tk.SUNKEN, padding=(5, 3))
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        self.status_var = tk.StringVar(value="Ready")
        self.status_lbl = ttk.Label(status_bar, textvariable=self.status_var, font=('Segoe UI', 9))
        self.status_lbl.pack(side=tk.LEFT)

        self.throughput_var = tk.StringVar(value="Throughput: 0 rec/s")
        self.throughput_lbl = ttk.Label(status_bar, textvariable=self.throughput_var, font=('Segoe UI', 9, 'bold'))
        self.throughput_lbl.pack(side=tk.RIGHT, padx=10)

    # ==========================================================
    # TAB 1: PIPELINE DASHBOARD & CONTROLS
    # ==========================================================
    def _build_dashboard_tab(self):
        # Configuration Card
        cfg_frame = ttk.LabelFrame(self.tab_dashboard, text=" Ingestion & Processing Configuration ", padding=15)
        cfg_frame.pack(fill=tk.X, pady=5)

        ttk.Label(cfg_frame, text="Dataset Source:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.file_path_var = tk.StringVar()
        file_entry = ttk.Entry(cfg_frame, textvariable=self.file_path_var, width=80)
        file_entry.grid(row=0, column=1, padx=10, sticky=tk.EW)

        browse_btn = ttk.Button(cfg_frame, text="Browse...", command=self._browse_file)
        browse_btn.grid(row=0, column=2, padx=5)

        ttk.Label(cfg_frame, text="Chunk Size:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.chunk_size_var = tk.IntVar(value=10000)
        chunk_combo = ttk.Combobox(cfg_frame, textvariable=self.chunk_size_var, values=[2000, 5000, 10000, 20000, 50000], width=12, state="readonly")
        chunk_combo.grid(row=1, column=1, sticky=tk.W, padx=10)

        # Control Buttons
        btn_frame = ttk.Frame(cfg_frame)
        btn_frame.grid(row=2, column=0, columnspan=3, pady=15, sticky=tk.W)

        self.start_btn = ttk.Button(btn_frame, text="▶ Run Processing Pipeline", style='Accent.TButton', command=self._start_pipeline)
        self.start_btn.pack(side=tk.LEFT, padx=5)

        self.cancel_btn = ttk.Button(btn_frame, text="⏹ Cancel", state=tk.DISABLED, command=self._cancel_pipeline)
        self.cancel_btn.pack(side=tk.LEFT, padx=5)

        self.export_report_btn = ttk.Button(btn_frame, text="📄 Export Executive HTML Report", state=tk.DISABLED, command=self._export_report)
        self.export_report_btn.pack(side=tk.LEFT, padx=10)

        # Live Execution Progress
        prog_frame = ttk.LabelFrame(self.tab_dashboard, text=" Live Execution Telemetry ", padding=15)
        prog_frame.pack(fill=tk.X, pady=10)

        self.progress_bar = ttk.Progressbar(prog_frame, orient=tk.HORIZONTAL, mode='determinate')
        self.progress_bar.pack(fill=tk.X, pady=5)

        metrics_grid = ttk.Frame(prog_frame)
        metrics_grid.pack(fill=tk.X, pady=5)

        self.lbl_processed = ttk.Label(metrics_grid, text="Processed Records: 0", font=('Segoe UI', 11, 'bold'))
        self.lbl_processed.pack(side=tk.LEFT, padx=15)

        self.lbl_dlq_count = ttk.Label(metrics_grid, text="Quarantined (DLQ): 0", font=('Segoe UI', 11, 'bold'), foreground='#b91c1c')
        self.lbl_dlq_count.pack(side=tk.LEFT, padx=15)

        self.lbl_heap_est = ttk.Label(metrics_grid, text="Memory Mode: Memory-Conscious Chunking Active", font=('Segoe UI', 10), foreground='#15803d')
        self.lbl_heap_est.pack(side=tk.RIGHT, padx=15)

        # Executive Summary Box
        summary_frame = ttk.LabelFrame(self.tab_dashboard, text=" Real-time Executive Insights ", padding=10)
        summary_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.summary_text = tk.Text(summary_frame, wrap=tk.WORD, font=('Consolas', 10), height=10)
        self.summary_text.pack(fill=tk.BOTH, expand=True)
        self.summary_text.insert(tk.END, "Application ready. Click 'Run Processing Pipeline' to ingest and analyze the dataset.")
        self.summary_text.config(state=tk.DISABLED)

    # ==========================================================
    # TAB 2: PEAK SALES
    # ==========================================================
    def _build_peak_sales_tab(self):
        container = ttk.Frame(self.tab_peak_sales)
        container.pack(fill=tk.BOTH, expand=True)

        # Matplotlib chart container
        self.fig_peak = Figure(figsize=(7, 4), dpi=100)
        self.ax_peak_hourly = self.fig_peak.add_subplot(121)
        self.ax_peak_daily = self.fig_peak.add_subplot(122)
        self.fig_peak.tight_layout()

        self.canvas_peak = FigureCanvasTkAgg(self.fig_peak, master=container)
        self.canvas_peak.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Workload summary table
        tbl_frame = ttk.LabelFrame(container, text=" Store-Level Workload & Peak Traffic ", padding=5)
        tbl_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=5)

        columns = ('store_id', 'total_tx', 'revenue', 'peak_hour')
        self.tree_peak = ttk.Treeview(tbl_frame, columns=columns, show='headings', height=5)
        self.tree_peak.heading('store_id', text='Store ID')
        self.tree_peak.heading('total_tx', text='Transactions')
        self.tree_peak.heading('revenue', text='Revenue ($)')
        self.tree_peak.heading('peak_hour', text='Busiest Window')
        self.tree_peak.pack(fill=tk.X)

    # ==========================================================
    # TAB 3: CUSTOMER SEGMENTATION
    # ==========================================================
    def _build_segmentation_tab(self):
        container = ttk.Frame(self.tab_segmentation)
        container.pack(fill=tk.BOTH, expand=True)

        self.fig_seg = Figure(figsize=(7, 4), dpi=100)
        self.ax_seg_clusters = self.fig_seg.add_subplot(121)
        self.ax_seg_age = self.fig_seg.add_subplot(122)
        self.fig_seg.tight_layout()

        self.canvas_seg = FigureCanvasTkAgg(self.fig_seg, master=container)
        self.canvas_seg.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        tbl_frame = ttk.LabelFrame(container, text=" Segment Performance Breakdown ", padding=5)
        tbl_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=5)

        columns = ('segment', 'count', 'revenue', 'avg_basket')
        self.tree_seg = ttk.Treeview(tbl_frame, columns=columns, show='headings', height=4)
        self.tree_seg.heading('segment', text='Customer Cluster')
        self.tree_seg.heading('count', text='Unique Customers')
        self.tree_seg.heading('revenue', text='Total Spend ($)')
        self.tree_seg.heading('avg_basket', text='Avg Basket Value ($)')
        self.tree_seg.pack(fill=tk.X)

    # ==========================================================
    # TAB 4: SEASONAL & PROMOTIONAL
    # ==========================================================
    def _build_seasonal_tab(self):
        container = ttk.Frame(self.tab_seasonal)
        container.pack(fill=tk.BOTH, expand=True)

        self.fig_seas = Figure(figsize=(7, 4), dpi=100)
        self.ax_seas_monthly = self.fig_seas.add_subplot(121)
        self.ax_seas_lift = self.fig_seas.add_subplot(122)
        self.fig_seas.tight_layout()

        self.canvas_seas = FigureCanvasTkAgg(self.fig_seas, master=container)
        self.canvas_seas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        tbl_frame = ttk.LabelFrame(container, text=" Promotional Campaign Ranking ", padding=5)
        tbl_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=5)

        columns = ('campaign', 'revenue', 'orders', 'avg_basket')
        self.tree_seas = ttk.Treeview(tbl_frame, columns=columns, show='headings', height=4)
        self.tree_seas.heading('campaign', text='Promotion Campaign')
        self.tree_seas.heading('revenue', text='Revenue Generated ($)')
        self.tree_seas.heading('orders', text='Promotional Orders')
        self.tree_seas.heading('avg_basket', text='Avg Ticket Size ($)')
        self.tree_seas.pack(fill=tk.X)

    # ==========================================================
    # TAB 5: REVENUE & PRODUCTS
    # ==========================================================
    def _build_revenue_tab(self):
        container = ttk.Frame(self.tab_revenue)
        container.pack(fill=tk.BOTH, expand=True)

        self.fig_rev = Figure(figsize=(7, 4), dpi=100)
        self.ax_rev_cat = self.fig_rev.add_subplot(121)
        self.ax_rev_channel = self.fig_rev.add_subplot(122)
        self.fig_rev.tight_layout()

        self.canvas_rev = FigureCanvasTkAgg(self.fig_rev, master=container)
        self.canvas_rev.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        tbl_frame = ttk.LabelFrame(container, text=" Top 10 Best-Selling Products (SKU) ", padding=5)
        tbl_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=5)

        columns = ('prod_name', 'category', 'units', 'revenue')
        self.tree_rev = ttk.Treeview(tbl_frame, columns=columns, show='headings', height=5)
        self.tree_rev.heading('prod_name', text='Product Name')
        self.tree_rev.heading('category', text='Category')
        self.tree_rev.heading('units', text='Units Sold')
        self.tree_rev.heading('revenue', text='Total Revenue ($)')
        self.tree_rev.pack(fill=tk.X)

    # ==========================================================
    # TAB 6: ANOMALY DETECTION
    # ==========================================================
    def _build_anomalies_tab(self):
        container = ttk.Frame(self.tab_anomalies)
        container.pack(fill=tk.BOTH, expand=True)

        # Upper Table: Sales volume outliers
        f1 = ttk.LabelFrame(container, text=" Daily Sales Drop & Volume Anomalies (Z-Score Outliers) ", padding=5)
        f1.pack(fill=tk.BOTH, expand=True, pady=3)

        cols1 = ('date', 'value', 'mean', 'z_score', 'severity', 'direction')
        self.tree_anom_vol = ttk.Treeview(f1, columns=cols1, show='headings', height=5)
        self.tree_anom_vol.heading('date', text='Date')
        self.tree_anom_vol.heading('value', text='Actual Revenue ($)')
        self.tree_anom_vol.heading('mean', text='Baseline Mean ($)')
        self.tree_anom_vol.heading('z_score', text='Z-Score (Sigma)')
        self.tree_anom_vol.heading('severity', text='Severity')
        self.tree_anom_vol.heading('direction', text='Anomaly Type')
        self.tree_anom_vol.pack(fill=tk.BOTH, expand=True)

        # Lower Table: Abnormal return rate stores
        f2 = ttk.LabelFrame(container, text=" Stores with High Return Rates (>= 7%) ", padding=5)
        f2.pack(fill=tk.BOTH, expand=True, pady=3)

        cols2 = ('store_id', 'sales', 'returns', 'rate', 'ret_amt', 'severity')
        self.tree_anom_ret = ttk.Treeview(f2, columns=cols2, show='headings', height=4)
        self.tree_anom_ret.heading('store_id', text='Store ID')
        self.tree_anom_ret.heading('sales', text='Total Sales')
        self.tree_anom_ret.heading('returns', text='Total Returns')
        self.tree_anom_ret.heading('rate', text='Return Rate (%)')
        self.tree_anom_ret.heading('ret_amt', text='Returned Value ($)')
        self.tree_anom_ret.heading('severity', text='Alert Level')
        self.tree_anom_ret.pack(fill=tk.BOTH, expand=True)

    # ==========================================================
    # TAB 7: STORE & REGIONAL PERFORMANCE
    # ==========================================================
    def _build_regional_tab(self):
        container = ttk.Frame(self.tab_regional)
        container.pack(fill=tk.BOTH, expand=True)

        self.fig_reg = Figure(figsize=(7, 4), dpi=100)
        self.ax_reg_share = self.fig_reg.add_subplot(121)
        self.ax_reg_stores = self.fig_reg.add_subplot(122)
        self.fig_reg.tight_layout()

        self.canvas_reg = FigureCanvasTkAgg(self.fig_reg, master=container)
        self.canvas_reg.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        tbl_frame = ttk.LabelFrame(container, text=" Regional Efficiency & Performance Rankings ", padding=5)
        tbl_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=5)

        columns = ('region', 'stores', 'revenue', 'share', 'avg_ticket')
        self.tree_reg = ttk.Treeview(tbl_frame, columns=columns, show='headings', height=4)
        self.tree_reg.heading('region', text='Region')
        self.tree_reg.heading('stores', text='Outlets')
        self.tree_reg.heading('revenue', text='Total Revenue ($)')
        self.tree_reg.heading('share', text='Revenue Share (%)')
        self.tree_reg.heading('avg_ticket', text='Avg Transaction ($)')
        self.tree_reg.pack(fill=tk.X)

    # ==========================================================
    # TAB 8: DEAD-LETTER QUEUE (DLQ)
    # ==========================================================
    def _build_dlq_tab(self):
        container = ttk.Frame(self.tab_dlq)
        container.pack(fill=tk.BOTH, expand=True)

        btn_bar = ttk.Frame(container)
        btn_bar.pack(fill=tk.X, pady=5)

        ttk.Button(btn_bar, text="💾 Export Full DLQ Audit Log to CSV", command=self._export_dlq).pack(side=tk.LEFT)
        self.dlq_status_lbl = ttk.Label(btn_bar, text="No records quarantined yet.", font=('Segoe UI', 10, 'italic'))
        self.dlq_status_lbl.pack(side=tk.LEFT, padx=15)

        cols = ('line', 'timestamp', 'reason', 'payload')
        self.tree_dlq = ttk.Treeview(container, columns=cols, show='headings')
        self.tree_dlq.heading('line', text='Line #')
        self.tree_dlq.heading('timestamp', text='Quarantine Time')
        self.tree_dlq.heading('reason', text='Failure Reason')
        self.tree_dlq.heading('payload', text='Raw Payload Sample')

        self.tree_dlq.column('line', width=70, stretch=False)
        self.tree_dlq.column('timestamp', width=140, stretch=False)
        self.tree_dlq.column('reason', width=220, stretch=False)
        self.tree_dlq.column('payload', width=600, stretch=True)

        scrollbar = ttk.Scrollbar(container, orient=tk.VERTICAL, command=self.tree_dlq.yview)
        self.tree_dlq.configure(yscroll=scrollbar.set)
        self.tree_dlq.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    # ==========================================================
    # ACTIONS & EVENT HANDLERS
    # ==========================================================
    def _browse_file(self):
        path = filedialog.askopenfilename(
            title="Select Retail Transactions Dataset",
            filetypes=[("CSV Files", "*.csv"), ("Text/Log Files", "*.txt;*.log;*.tsv"), ("All Files", "*.*")]
        )
        if path:
            self.file_path_var.set(path)
            self.status_var.set(f"Selected file: {os.path.basename(path)}")

    def _start_pipeline(self):
        path = self.file_path_var.get().strip()
        if not path or not os.path.exists(path):
            messagebox.showerror("File Error", "Please provide a valid transaction dataset file path.")
            return

        chunk_size = self.chunk_size_var.get()

        self.is_processing = True
        self.start_btn.config(state=tk.DISABLED)
        self.cancel_btn.config(state=tk.NORMAL)
        self.export_report_btn.config(state=tk.DISABLED)
        self.progress_bar['value'] = 0

        # Clear UI tables
        for tree in (self.tree_peak, self.tree_seg, self.tree_seas, self.tree_rev, self.tree_anom_vol, self.tree_anom_ret, self.tree_reg, self.tree_dlq):
            for row in tree.get_children():
                tree.delete(row)

        self.status_var.set("Configuring pipeline and initializing worker...")

        # Run pipeline in a background thread to keep GUI responsive
        worker = threading.Thread(target=self._run_worker, args=(path, chunk_size), daemon=True)
        worker.start()

    def _run_worker(self, path: str, chunk_size: int):
        try:
            self.facade.configure_pipeline(path, chunk_size)
            self.facade.execute_pipeline()
        except Exception as e:
            self.on_error(str(e))

    def _cancel_pipeline(self):
        if self.is_processing:
            self.facade.cancel()
            self.status_var.set("Cancelling pipeline execution...")

    def _export_report(self):
        if not self.current_results:
            return
        out_path = filedialog.asksaveasfilename(
            defaultextension=".html",
            filetypes=[("HTML Report", "*.html")],
            initialfile="smartmart_executive_report.html"
        )
        if out_path:
            ReportExporter.export_html_report(self.current_results, out_path)
            messagebox.showinfo("Export Successful", f"Executive report generated:\n{out_path}")

    def _export_dlq(self):
        out_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv")],
            initialfile="smartmart_dlq_audit.csv"
        )
        if out_path:
            self.facade.get_dlq().export_audit_log(out_path)
            messagebox.showinfo("Export Successful", f"DLQ audit log exported to:\n{out_path}")

    # ==========================================================
    # OBSERVER CALLBACKS (Invoked from background thread)
    # ==========================================================
    def on_progress_update(self, processed_count: int, estimated_total: int, throughput_rps: float) -> None:
        def update():
            pct = (processed_count / max(1, estimated_total)) * 100.0
            self.progress_bar['value'] = min(100.0, pct)
            self.lbl_processed.config(text=f"Processed Records: {processed_count:,}")
            self.throughput_var.set(f"Throughput: {throughput_rps:,.0f} rec/s")
            self.status_var.set(f"Streaming chunk batches... ({pct:.1f}%)")
        self.after(0, update)

    def on_dlq_alert(self, faulty_record: FaultyRecord, current_failure_count: int) -> None:
        def update():
            self.lbl_dlq_count.config(text=f"Quarantined (DLQ): {current_failure_count:,}")
            self.dlq_status_lbl.config(text=f"Quarantined {current_failure_count:,} faulty records safely in DLQ.")
            if len(self.tree_dlq.get_children()) < 100:
                self.tree_dlq.insert('', 'end', values=(
                    faulty_record.line_number,
                    faulty_record.timestamp.strftime('%H:%M:%S'),
                    faulty_record.failure_reason,
                    faulty_record.raw_payload[:120]
                ))
        self.after(0, update)

    def on_pipeline_complete(self, results: Dict[str, AnalyticsResult]) -> None:
        def update():
            self.current_results = results
            self.is_processing = False
            self.start_btn.config(state=tk.NORMAL)
            self.cancel_btn.config(state=tk.DISABLED)
            self.export_report_btn.config(state=tk.NORMAL)
            self.progress_bar['value'] = 100.0
            self.status_var.set("Pipeline execution completed successfully!")

            # Refresh All Views
            self._render_peak_sales(results.get('peak_sales'))
            self._render_segmentation(results.get('customer_segmentation'))
            self._render_seasonal(results.get('seasonal_promotional'))
            self._render_revenue(results.get('revenue_product'))
            self._render_anomalies(results.get('anomaly_detection'))
            self._render_regional(results.get('store_regional'))

            # Update Executive Summary
            self.summary_text.config(state=tk.NORMAL)
            self.summary_text.delete('1.0', tk.END)
            for k, res in results.items():
                self.summary_text.insert(tk.END, f"• [{res.engine_name.upper()}]: {res.summary_text}\n\n")
            self.summary_text.config(state=tk.DISABLED)

            messagebox.showinfo("Analysis Complete", "Dataset processed successfully! Explore analytical insights across tabs.")
        self.after(0, update)

    def on_error(self, error_message: str) -> None:
        def update():
            self.is_processing = False
            self.start_btn.config(state=tk.NORMAL)
            self.cancel_btn.config(state=tk.DISABLED)
            self.status_var.set(f"Error: {error_message}")
            messagebox.showerror("Pipeline Failure", f"An error occurred during execution:\n{error_message}")
        self.after(0, update)

    # ==========================================================
    # RENDERING METHODS
    # ==========================================================
    def _render_peak_sales(self, res: Optional[AnalyticsResult]):
        if not res: return
        m = res.metrics

        # Hourly Chart
        self.ax_peak_hourly.clear()
        hours = list(m['hourly_tx_count'].keys())
        counts = list(m['hourly_tx_count'].values())
        self.ax_peak_hourly.bar(hours, counts, color='#3b82f6')
        self.ax_peak_hourly.set_title("Hourly Transaction Traffic (0-23h)", fontsize=9, fontweight='bold')
        self.ax_peak_hourly.set_xlabel("Hour of Day", fontsize=8)
        self.ax_peak_hourly.set_ylabel("Transactions", fontsize=8)

        # Daily Chart
        self.ax_peak_daily.clear()
        days = list(m['daily_tx_count'].keys())
        d_counts = list(m['daily_tx_count'].values())
        self.ax_peak_daily.bar([d[:3] for d in days], d_counts, color='#10b981')
        self.ax_peak_daily.set_title("Day of Week Traffic", fontsize=9, fontweight='bold')
        self.ax_peak_daily.set_xlabel("Day", fontsize=8)

        self.fig_peak.tight_layout()
        self.canvas_peak.draw()

        # Table
        for s in m['store_workload_summary'][:15]:
            self.tree_peak.insert('', 'end', values=(s['store_id'], f"{s['total_tx']:,}", f"${s['total_revenue']:,.2f}", s['peak_hour']))

    def _render_segmentation(self, res: Optional[AnalyticsResult]):
        if not res: return
        m = res.metrics

        # Cluster Pie Chart
        self.ax_seg_clusters.clear()
        cl_data = m['cluster_summary']
        labels = list(cl_data.keys())
        sizes = [cl_data[k]['customer_count'] for k in labels]
        self.ax_seg_clusters.pie(sizes, labels=labels, autopct='%1.1f%%', colors=['#2563eb', '#f59e0b', '#94a3b8'], startangle=140)
        self.ax_seg_clusters.set_title("Customer Segmentation Mix", fontsize=9, fontweight='bold')

        # Age Demographics
        self.ax_seg_age.clear()
        ages = list(m['age_group_spend'].keys())
        age_spend = [m['age_group_spend'][a] for a in ages]
        self.ax_seg_age.bar(ages, age_spend, color='#8b5cf6')
        self.ax_seg_age.set_title("Spending by Age Demographic ($)", fontsize=9, fontweight='bold')
        self.ax_seg_age.tick_params(axis='x', rotation=30)

        self.fig_seg.tight_layout()
        self.canvas_seg.draw()

        for k, v in cl_data.items():
            self.tree_seg.insert('', 'end', values=(k, f"{v['customer_count']:,}", f"${v['total_revenue']:,.2f}", f"${v['avg_basket_value']:.2f}"))

    def _render_seasonal(self, res: Optional[AnalyticsResult]):
        if not res: return
        m = res.metrics

        # Monthly line trend
        self.ax_seas_monthly.clear()
        months = [k[:3] for k in m['monthly_revenue'].keys()]
        revs = list(m['monthly_revenue'].values())
        self.ax_seas_monthly.plot(months, revs, marker='o', color='#ea580c', linewidth=2)
        self.ax_seas_monthly.set_title("Seasonal Demand Curve (Monthly Revenue)", fontsize=9, fontweight='bold')
        self.ax_seas_monthly.set_ylabel("Revenue ($)", fontsize=8)
        self.ax_seas_monthly.tick_params(axis='x', rotation=45)

        # Lift comparison
        self.ax_seas_lift.clear()
        categories = ['Baseline', 'Promotional']
        tickets = [m['avg_baseline_ticket'], m['avg_promo_ticket']]
        bars = self.ax_seas_lift.bar(categories, tickets, color=['#94a3b8', '#16a34a'])
        self.ax_seas_lift.set_title(f"Promotional Basket Lift ({m['promotional_lift_percent']:+.1f}%)", fontsize=9, fontweight='bold')
        self.ax_seas_lift.set_ylabel("Avg Ticket Size ($)", fontsize=8)

        self.fig_seas.tight_layout()
        self.canvas_seas.draw()

        for c in m['campaign_breakdown'][:10]:
            self.tree_seas.insert('', 'end', values=(c['campaign_name'], f"${c['revenue']:,.2f}", f"{c['tx_count']:,}", f"${c['avg_basket']:.2f}"))

    def _render_revenue(self, res: Optional[AnalyticsResult]):
        if not res: return
        m = res.metrics

        # Categories
        self.ax_rev_cat.clear()
        cats = list(m['category_revenue'].keys())[:7]
        cat_rev = [m['category_revenue'][c] for c in cats]
        self.ax_rev_cat.barh(cats[::-1], cat_rev[::-1], color='#0284c7')
        self.ax_rev_cat.set_title("Top Category Revenues ($)", fontsize=9, fontweight='bold')

        # Channel
        self.ax_rev_channel.clear()
        chans = list(m['channel_breakdown'].keys())
        chan_rev = list(m['channel_breakdown'].values())
        self.ax_rev_channel.pie(chan_rev, labels=chans, autopct='%1.1f%%', colors=['#0d9488', '#6366f1'])
        self.ax_rev_channel.set_title("Sales Channel Share", fontsize=9, fontweight='bold')

        self.fig_rev.tight_layout()
        self.canvas_rev.draw()

        for p in m['top_products']:
            self.tree_rev.insert('', 'end', values=(p['product_name'], p['category'], f"{p['units']:,}", f"${p['revenue']:,.2f}"))

    def _render_anomalies(self, res: Optional[AnalyticsResult]):
        if not res: return
        m = res.metrics

        for a in m['daily_sales_anomalies']:
            self.tree_anom_vol.insert('', 'end', values=(
                a['date'], f"${a['value']:,.2f}", f"${a['mean']:,.2f}", f"{a['z_score']:+.2f}", a['severity'], a['direction']
            ))

        for r in m['abnormal_return_stores']:
            self.tree_anom_ret.insert('', 'end', values=(
                r['store_id'], f"{r['sales_count']:,}", f"{r['returns_count']:,}", f"{r['return_rate_percent']:.2f}%", f"${r['returns_amount']:,.2f}", r['severity']
            ))

    def _render_regional(self, res: Optional[AnalyticsResult]):
        if not res: return
        m = res.metrics

        # Regional Share
        self.ax_reg_share.clear()
        reg_data = m['regional_summary']
        regs = list(reg_data.keys())
        shares = [reg_data[r]['revenue_share_percent'] for r in regs]
        self.ax_reg_share.pie(shares, labels=regs, autopct='%1.1f%%', startangle=90)
        self.ax_reg_share.set_title("Regional Revenue Contribution", fontsize=9, fontweight='bold')

        # Top 5 Stores
        self.ax_reg_stores.clear()
        top5 = m['top_5_stores']
        s_names = [f"{s['store_id']}\n({s['city']})" for s in top5]
        s_revs = [s['revenue'] for s in top5]
        self.ax_reg_stores.bar(s_names, s_revs, color='#10b981')
        self.ax_reg_stores.set_title("Top 5 Performing Stores ($)", fontsize=9, fontweight='bold')
        self.ax_reg_stores.tick_params(axis='x', rotation=20)

        self.fig_reg.tight_layout()
        self.canvas_reg.draw()

        for r_name, r in reg_data.items():
            self.tree_reg.insert('', 'end', values=(r_name, r['store_count'], f"${r['total_revenue']:,.2f}", f"{r['revenue_share_percent']}%", f"${r['average_transaction_value']:.2f}"))


def main():
    app = SmartMartApp()
    app.mainloop()


if __name__ == '__main__':
    main()
