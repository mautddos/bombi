import random
import time
import requests
from collections import Counter
import matplotlib.pyplot as plt
from datetime import datetime

class WingoAIAnalyzer:
    def __init__(self):
        # Game rules
        self.SMALL_NUMS = [1, 2, 3, 4]
        self.BIG_NUMS = [5, 6, 7, 8, 9]
        self.GREEN_NUMS = {1, 3, 7, 9, 2, 4, 6, 8}
        self.HALF_GREEN = {0, 5}
        self.PERIODS = ['30s', '1m', '3m', '5m']
        self.history = []
        self.ai_endpoint = "https://api.smtv.uz/ai/index.php"
        
    def generate_history(self, rounds=500):
        """Generate realistic historical data with period simulation"""
        for _ in range(rounds):
            num = random.choices(
                list(range(10)),
                weights=[5, 8, 12, 15, 10, 10, 15, 12, 8, 5]
            )[0]
            
            color = ('green' if num in self.GREEN_NUMS else 
                    random.choice(['red', 'green']) if num in self.HALF_GREEN else 
                    'red')
            
            self.history.append({
                'number': num,
                'color': color,
                'size': 'small' if num in self.SMALL_NUMS else 'big',
                'period': random.choices(self.PERIODS, weights=[40, 30, 20, 10])[0],
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
        return self.history
    
    def ai_predict(self, trend_data):
        """Simulate AI prediction using external API (educational mock)"""
        try:
            # Mock AI response - in reality this would require proper API integration
            mock_responses = [
                {"prediction": "green", "confidence": 65},
                {"prediction": "red", "confidence": 70},
                {"prediction": random.choice(["30s", "1m"]), "confidence": 60}
            ]
            return random.choice(mock_responses)
        except:
            return {"prediction": "green", "confidence": 55}  # Fallback
    
    def analyze_trends(self):
        """Advanced analysis with period tracking"""
        analysis = {
            'numbers': Counter([x['number'] for x in self.history[-50:]]),
            'colors': Counter([x['color'] for x in self.history[-20:]]),
            'periods': Counter([x['period'] for x in self.history[-30:]]),
            'sizes': Counter([x['size'] for x in self.history[-15:]])
        }
        
        # AI-enhanced prediction
        ai_color = self.ai_predict(analysis['colors'])
        ai_period = self.ai_predict(analysis['periods'])
        
        return {
            'hot_number': analysis['numbers'].most_common(1)[0][0],
            'cold_number': analysis['numbers'].most_common()[-1][0],
            'likely_color': ai_color['prediction'],
            'color_confidence': ai_color['confidence'],
            'likely_period': ai_period['prediction'],
            'period_confidence': ai_period['confidence'],
            'likely_size': analysis['sizes'].most_common(1)[0][0]
        }
    
    def auto_mode(self, interval=30):
        """Auto-prediction mode with simulated delays"""
        print("🚀 Auto-Prediction Mode Activated (Educational Use Only)")
        print("Press Ctrl+C to stop\n")
        
        try:
            while True:
                prediction = self.predict_next()
                print(f"\n⏰ Period: {prediction['period']} ({prediction['period_confidence']}%)")
                print(f"🔢 Number: {prediction['number']} | Color: {prediction['color'].upper()}")
                print(f"📏 Size: {prediction['size'].upper()} | Confidence: {prediction['confidence']}%")
                print("─" * 40)
                time.sleep(interval)
        except KeyboardInterrupt:
            print("\nAuto-mode stopped")

    def predict_next(self):
        """Generate comprehensive prediction"""
        if not self.history:
            self.generate_history()
            
        trends = self.analyze_trends()
        
        return {
            'number': trends['hot_number'] if random.random() > 0.4 else trends['cold_number'],
            'color': trends['likely_color'],
            'size': trends['likely_size'],
            'period': trends['likely_period'],
            'confidence': trends['color_confidence'],
            'period_confidence': trends['period_confidence']
        }

    def show_dashboard(self):
        """Interactive visualization dashboard"""
        plt.figure(figsize=(15, 10))
        
        # Number distribution
        plt.subplot(2, 2, 1)
        nums = [x['number'] for x in self.history]
        plt.hist(nums, bins=10, color='skyblue')
        plt.title("Number Frequency (Last 500 Rounds)")
        
        # Period distribution
        plt.subplot(2, 2, 2)
        periods = [x['period'] for x in self.history]
        period_counts = Counter(periods)
        plt.pie(
            period_counts.values(),
            labels=period_counts.keys(),
            autopct='%1.1f%%',
            colors=['gold', 'lightcoral', 'lightskyblue', 'lightgreen']
        )
        plt.title("Period Distribution")
        
        # Color ratio
        plt.subplot(2, 2, 3)
        colors = [x['color'] for x in self.history]
        color_counts = Counter(colors)
        plt.bar(
            color_counts.keys(),
            color_counts.values(),
            color=['red', 'green']
        )
        plt.title("Color Ratio")
        
        # Size ratio
        plt.subplot(2, 2, 4)
        sizes = [x['size'] for x in self.history]
        size_counts = Counter(sizes)
        plt.bar(
            size_counts.keys(),
            size_counts.values(),
            color=['blue', 'orange']
        )
        plt.title("Size Ratio")
        
        plt.tight_layout()
        plt.show()

# Main execution
if __name__ == "__main__":
    analyzer = WingoAIAnalyzer()
    analyzer.generate_history()
    
    print("=== 🎰 Wingo AI Predictor Simulator ===")
    print("Disclaimer: This is for educational purposes only\n")
    
    while True:
        print("\n1. Get Prediction\n2. Auto Mode\n3. Show Dashboard\n4. Exit")
        choice = input("Select mode: ")
        
        if choice == "1":
            pred = analyzer.predict_next()
            print(f"\n🎯 Prediction Results:")
            print(f"Period: {pred['period']} ({pred['period_confidence']}% confidence)")
            print(f"Number: {pred['number']} | Color: {pred['color'].upper()}")
            print(f"Size: {pred['size'].upper()} | Overall Confidence: {pred['confidence']}%")
            
        elif choice == "2":
            analyzer.auto_mode(interval=15)  # 15-second intervals
            
        elif choice == "3":
            analyzer.show_dashboard()
            
        elif choice == "4":
            print("Exiting simulator...")
            break
