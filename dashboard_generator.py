import json
import os
from datetime import datetime

def generate_dashboard(invoices, aggregated_categories, ai_analysis):
    print("Generating Dashboard...")
    
    # Sort invoices by date for the trend chart
    invoices.sort(key=lambda x: x.date if x.date else datetime.min.date())
    
    # Prepare Category Chart data
    cat_labels = list(aggregated_categories.keys())
    cat_data = list(aggregated_categories.values())
    
    # Prepare Trend Chart data
    trend_labels = [str(inv.date) if inv.date else "Unknown" for inv in invoices]
    trend_data = [inv.total_amount for inv in invoices]
    
    # Simple HTML Template
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Invoice Expense Dashboard</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    </head>
    <body class="bg-gray-100 font-sans leading-normal tracking-normal">
        <div class="container mx-auto px-4 py-8">
            <h1 class="text-4xl font-bold text-gray-800 mb-8 text-center">Expense Analysis Dashboard</h1>
            
            <div class="grid grid-cols-1 md:grid-cols-2 gap-8 mb-8">
                <!-- Category Chart Section -->
                <div class="bg-white rounded-lg shadow-lg p-6">
                    <h2 class="text-2xl font-bold mb-4 text-gray-700">Spending by Category</h2>
                    <canvas id="expenseChart"></canvas>
                </div>
                
                <!-- AI Summary Section -->
                <div class="bg-white rounded-lg shadow-lg p-6 overflow-y-auto" style="max-height: 500px;">
                    <h2 class="text-2xl font-bold mb-4 text-gray-700">AI Executive Summary</h2>
                    <div class="prose max-w-none text-gray-600">
                        {ai_analysis.replace(chr(10), '<br>')} 
                    </div>
                </div>
            </div>
            
            <!-- Trend Chart Section -->
            <div class="bg-white rounded-lg shadow-lg p-6">
                <h2 class="text-2xl font-bold mb-4 text-gray-700">Spending Trend (Total per Invoice)</h2>
                <div class="relative h-64 md:h-96">
                     <canvas id="trendChart"></canvas>
                </div>
            </div>
        </div>

        <script>
            // Category Pie Chart
            const ctx = document.getElementById('expenseChart').getContext('2d');
            new Chart(ctx, {{
                type: 'doughnut',
                data: {{
                    labels: {json.dumps(cat_labels)},
                    datasets: [{{
                        data: {json.dumps(cat_data)},
                        backgroundColor: [
                            '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#FF9F40', 
                            '#E7E9ED', '#76A346', '#FDB45C', '#949FB1', '#4D5360', '#B4F8C8', '#FFAEB9'
                        ]
                    }}]
                }},
                options: {{
                    responsive: true,
                    plugins: {{
                        legend: {{ position: 'bottom' }}
                    }}
                }}
            }});
            
            // Trend Bar Chart
            const ctxTrend = document.getElementById('trendChart').getContext('2d');
            new Chart(ctxTrend, {{
                type: 'bar',
                data: {{
                    labels: {json.dumps(trend_labels)},
                    datasets: [{{
                        label: 'Invoice Total ($)',
                        data: {json.dumps(trend_data)},
                        backgroundColor: '#36A2EB',
                        borderColor: '#2482C2',
                        borderWidth: 1
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {{
                        y: {{
                            beginAtZero: true,
                            title: {{
                                display: true,
                                text: 'Amount ($)'
                            }}
                        }},
                        x: {{
                             title: {{
                                display: true,
                                text: 'Date'
                            }}
                        }}
                    }}
                }}
            }});
        </script>
    </body>
    </html>
    """
    
    with open("dashboard.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"Dashboard saved to {os.path.abspath('dashboard.html')}")
