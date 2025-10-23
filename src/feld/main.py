import sys
import os
import time
import random
import math

# config
START_LUX = 10000 # remember, lux is the currency
STABILITY_DECAY = 0.01

# utility
def clear(): 
    os.system("cls" if os.name == "nt" else "clear")

def format_text(text: str, codes: list) -> str:  # use ascii escapes natively instead of heavy dependent modules
    # codes: list of either color code or a tuple with (background: bool, int, int, int)
    colors = {
        # terminal utility codes
        "reset": "\x1b[0m",
        "home": "\x1b[H",
        "clear": "\x1b[2J",
        "clearline": "\x1b[2K",
        
        # formatting codes
        "bold": "\x1b[1m",
        "italic": "\x1b[3m",
        "underline": "\x1b[4m",
        "blinking": "\x1b[5m",
        "inverse": "\x1b[7m",
        "strikethrough": "\x1b[9m",
        
        # colors
        "red": "\x1b[31m",
        "yellow": "\x1b[33m",
        "green": "\x1b[32m",
        "cyan": "\x1b[36m",
        "blue": "\x1b[34m",
        "magenta": "\x1b[35m",
        "white": "\x1b[37m",
        "black": "\x1b[30m",
        "default": "\x1b[m",
        
        # bright colors
        "bright_black": "\x1b[90m",
        "bright_red": "\x1b[91m",
        "bright_green": "\x1b[92m",
        "bright_yellow": "\x1b[93m",
        "bright_blue": "\x1b[94m",
        "bright_magenta": "\x1b[95m",
        "bright_cyan": "\x1b[96m",
        "bright_white": "\x1b[97m",
    }
    
    buffer = ""
    if not isinstance(codes, list):
        raise TypeError(f"'codes' should be a list, even if with only one element. Found {type(codes)} instead.")
    if not isinstance(text, str):
        raise TypeError(f"'text' should be a string, found {type(text)} instead.")
    
    for code in codes:
        if isinstance(code, str):
            buffer += colors.get(code,"")
            
        elif isinstance(code, tuple):
            if not isinstance(code[0], bool):
                raise ValueError(f"Should be bool defining whether this is a background color, found {type(code[0])} instead.")
            if len(code) != 4:
                raise ValueError(f"Tuple should have four elements: (bool, r, g, b), found {len(code)}.")
            for i in code[1:]:
                if not isinstance(i, int):
                    raise ValueError(f"RGB must be integers, found {type(i)}.")
                if not (0 <= i <= 255):
                    raise ValueError(f"RGB numbers should be under 255 and at least 0, found {i} instead")
                
            final = f"\x1b[{48 if code[0] else 38};2;{code[1]};{code[2]};{code[3]}m"
            buffer += final
            
        else:
            raise TypeError(f"List 'codes' should only contain strings or tuples, found {type(code)} instead.")
        
    return f"{buffer}{text}{colors["reset"]}"

def glitch(text: str, intensity: float, glitch_characters: str = "#$@%&^/?X") -> str: # terminal glitch effect
    # TODO: Add unicode glitch chars? random generation capability? unicode lookalike table? a polish effect
    # intensity: percentage of chars to glitch, 0.0 -> 1.0
    chars = list(text)
    for i in range(len(chars)):
        if random.random < intensity:
            chars[i] = random.choice(glitch_characters)
    return "".join(chars)

GRAPH_CHARS = "▁▂▃▄▅▆▇█"
def sparkline(history, width = 20):
    if not history:
        return ""
    
    vals = history[-width:]
    lo, hi = min(vals), max(vals)
    if hi - lo < 1e-6:
        return "".join(format_text(GRAPH_CHARS[0], ["bright_cyan"]) for _ in vals)
    
    span = hi-lo
    scaled = [(v - lo) / span for v in vals]
    
    parts = []
    for i, s in enumerate(scaled):
        ch = GRAPH_CHARS[int(s * (len(GRAPH_CHARS) - 1))]
        if i == 0:
            color = "bright_cyan"
        else:
            diff = vals[i] - vals[i - 1]
            if diff > 0.1:
                color = "bright_green"
            elif diff < -0.1:
                color = "bright_red"
            else:
                color = "bright_cyan"
        parts.append(format_text(ch, [color]))
        
    return "".join(parts)

# classes
class Asset: # subclass to be used only under Market
    def __init__(self, name, base, volatility, trend):
        self.name = name      # Name of asset
        self.price = base     # Base (starting) price
        self.vol = volatility # Standard deviation on random
        self.trend = trend    # Trend directional drift
        self.last_change = 0  # For stock tracker
        
    def update(self, temp, stability):
        delta = self.trend + random.gauss(0, self.vol)
        instability = (1 - stability)
        change = delta + temp * instability
        old = self.price
        self.price = max(0.1, self.price * (1 + change))
        self.last_change = self.price - old
    
class Market:
    def __init__(self):
        self.assets = [ # TODO: Add json parsing here
            Asset("Helios Corp.", 100, -0.02, -0.001), # TODO: Trend should be random maybe?
            Asset("Photonic Semiconductors Limited", 40, 0.06, -0.002), # TODO: Add more asset types obviously
            Asset("Ionic Compound Manufacturers", 30, 0.0, 0.0)
        ] 
        self.stability = 1.0
        self.temp = 0.0
        self.cycle = 0
    
    def tick(self):
        for a in self.assets:
            a.update(self.temp, self.stability)
        self.stability = max(0, self.stability - STABILITY_DECAY)
        self.temp += random.uniform(-0.01, 0.02)
        self.cycle += 1
        
    def summary(self):
        print(format_text(f"\n[Market Stability: {self.stability:.2f}]   [Cycle {self.cycle}]\n", ["bright_cyan"]))
        for a in self.assets:
            col = "bright_green" if a.last_change > 0 else "bright_red" if a.last_change < 0 else "bright_cyan"
            sym = "⌃" if a.last_change > 0 else "⌄" if a.last_change < 0 else "~"
            print(f"{a.name:32} | {format_text(f"{sym} {a.last_change:5.2f}", [col])}", format_text(f"(Ⱡ{a.price:.2f})", [col]))
        
    
class Player:
    pass

# logic
def handle_buy(player, market, arg):
    pass

def handle_sell(player, market, arg):
    pass

def handle_supplies(player):
    pass

def show_status(player, market):
    pass

def get_technobabble(stability):
    pass

def game_end(player, market):
    pass

# loop
def main():
    market = Market()
    while(True):
        market.summary()
        market.tick()
        time.sleep(0.02)
    
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(format_text("test", ["bold", (False, 255, 80, 80), "bold", "underline"]))