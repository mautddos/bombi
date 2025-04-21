import random
import time
from datetime import datetime
from collections import Counter
import matplotlib.pyplot as plt

# Simulated Wingo Game Data (for educational purposes)
class WingoSimulator:
    def __init__(self):
        self.history = []
        self.colors = ['red', 'green']
        self.numbers = list(range(10))  # 0-9
        self.time_periods = ['30s', '1m']
        self.sizes = ['big', 'small']
        
    def generate_fake_history(self, entries=100):
        """Simulates past game results (weighted randomness)"""
        for _ in range(entries):
            entry = {
                'time': datetime.now().strftime("%H:%M:%S"),
                'color': random.choices(self.colors, weights=[55, 45])[0],  # Slight red bias
                'number': random.choices(self.numbers, weights=[8,9,10,11,12,13,12,11,10,9])[0],  # Middle numbers more common
                'period': random.choice(self.time_periods),
                'size': random.choices(self.sizes, weights=[52, 48])[0]  # Slight big bias
            }
            self.history.append(entry)
        return self.history
    
    def analyze_trends(self, last_n=20):
        """Analyzes recent trends for predictions"""
        recent = self.history[-last_n:]
        
        # Color Analysis
        color_count = Counter([x['color'] for x in recent])
        likely_color = color_count.most_common(1)[0][0]
        
        # Number Analysis (cold numbers)
        all_numbers = [x['number'] for x in self.history]
        cold_numbers = [n for n in self.numbers if all_numbers.count(n) == min(all_numbers.count(num) for num in self.numbers)]
        
        # Time Period Analysis
        period_count = Counter([x['period'] for x in recent])
        likely_period = period_count.most_common(1)[0][0]
        
        # Size Analysis
        size_count = Counter([x['size'] for x in recent])
        likely_size = size_count.most_common(1)[0][0]
        
        return {
            'likely_color': likely_color,
            'cold_numbers': cold_numbers,
            'likely_period': likely_period,
            'likely_size': likely_size,
            'confidence': random.randint(65, 80)  # Simulated confidence
        }
    
    def predict_next(self):
        """Generates a prediction based on trends"""
        if not self.history:
            self.generate_fake_history(50)
        
        trends = self.analyze_trends()
        
        return {
            'predicted_color': trends['likely_color'],
            'predicted_number': random.choice(trends['cold_numbers']),
            'predicted_period': trends['likely_period'],
            'predicted_size': trends['likely_size'],
            'confidence': trends['confidence']
        }
    
    def show_stats(self):
        """Displays historical statistics"""
        colors = [x['color'] for x in self.history]
        numbers = [x['number'] for x in self.history]
        
        print("\n=== Historical Stats ===")
        print(f"Total Rounds: {len(self.history)}")
        print(f"Red/Green Ratio: {colors.count('red')}/{colors.count('green')}")
        print(f"Most Common Number: {Counter(numbers).most_common(1)[0][0]}")
        print(f"Cold Numbers: {[n for n in self.numbers if numbers.count(n) == min(numbers.count(num) for num in self.numbers)]}")

# Main Program
if __name__ == "__main__":
    print("=== Wingo Game Analyzer (Educational Simulation) ===")
    print("Disclaimer: This does NOT connect to any real website.\n")
    
    simulator = WingoSimulator()
    simulator.generate_fake_history(100)  # Simulate 100 past games
    
    while True:
        try:
            input("\nPress Enter to Generate Prediction (Ctrl+C to Exit)...")
            prediction = simulator.predict_next()
            
            print("\n=== Prediction Results ===")
            print(f"Color: {prediction['predicted_color'].upper()}")
            print(f"Number (from cold numbers): {prediction['predicted_number']}")
            print(f"Time Period: {prediction['predicted_period']}")
            print(f"Size: {prediction['predicted_size'].upper()}")
            print(f"Confidence: {prediction['confidence']}%")
            
            simulator.show_stats()  # Show historical trends
            
        except KeyboardInterrupt:
            print("\nExiting simulator...")
            break
