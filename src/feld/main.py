# TODO: Fix Asset and Market classes


import sys
import os
import time
import random
import math # you know when you see this that you're about to have a baaaad time

# config
START_LUX = 10000 # lux is the currency
CYCLES_TOTAL = 100
TICK_RATE = 2.5

HAB_COST = 50000 # so 5x to win? might be impossible, playtest needed
SUPPLY_COST = 500 # x 100, so we have another 50,000 required here
SUPPLY_START = 5
SUPPLY_CONS = 1 # per cycle, but this might need to be lower

# utility
def clear(): 
    os.system("cls" if os.name == "nt" else "clear") # probably better to use escape chars

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
        # TODO: These might not work on every terminal, consider switching to program-defined ones?
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
        
    return f"{buffer}{text}{colors['reset']}"

def glitch(text: str, intensity: float, glitch_characters: str = "#$@%&^/?X") -> str: # terminal glitch effect
    # TODO: Add unicode glitch chars? random generation capability? unicode lookalike table? a polish effect
    # intensity: percentage of chars to glitch, 0.0 -> 1.0
    if not 0 <= intensity <= 1:
        raise ValueError("intensity must be between 0.0 and 1.0")
    chars = list(text)
    for i in range(len(chars)):
        if random.random() < intensity:
            chars[i] = random.choice(glitch_characters)
    return "".join(chars)

GRAPH_CHARS = "▁▂▃▄▅▆▇█"

def sparkline(history, width = 20):
    if not history:
        return ""
    
    vals = history[-width:]
    lo, hi = min(vals), max(vals)
    n = len(vals)
    
    if hi - lo < 1e-9:
        return "".join(format_text(GRAPH_CHARS[0], ["yellow"]) for _ in vals)
    
    span = hi - lo
    scaled = [int((v - lo) / span * (len(GRAPH_CHARS) - 1)) for v in vals]
    slope = vals[-1] - vals[0]
    avg_step = sum(abs(vals[i+1] - vals[i]) for i in range(n-1)) / max(1, n-1)
    
    if abs(slope) < max(0.1, 0,5 * avg_step):
        col = "yellow"
    elif slope > 0:
        col = "bright_green"
    else:
        col = "bright_red"
    
    parts = [format_text(GRAPH_CHARS[idx], [col]) for idx in scaled]
    return "".join(parts)

# classes
class Asset: # subclass to be used only under Market
    def __init__(self, name, base, volatility, resilience = 1.0):
        self.name = name      # Name of asset
        self.price = base     # Base (starting) price
        self.volatility = volatility # Standard deviation on random 
        self.resilience = resilience # how easily it will decay when the market collapses (how much power it consumes)
        self.trend = random.uniform(-0.05, 0.05) # bias per asset, keeps believable strings of up and down
        self.last_change = 0  # For stock tracker
        self.history = [base]
        self.delisted = False
        
    def update(self, stability: float):
        self.t += 1
        if self.delisted:
            self.price = 0.0
            self.last_change = 0.0
            return
        
        prev = self.price
        
        decay_factor = max(0, 1.0 - stability)
        sensitivity = decay_factor * (1 / self.resilience)
        trend_force = self.trend * (0.3 + stability)
        random_fluct = random.uniform(-self.volatility, self.volatility)
        delta_pct = trend_force - sensitivity + random_fluct
        delta = self.price * delta_pct
        
        self.price += delta #airlines (always falling)
        if self.price < 0:
            self.price = 0
        self.last_change = self.price - prev
        self.history.append(self.price)
        
        if self.price <= 0.5:
            self.delisted = True
    
        # the sine shit isnt here any more thank god
    
class Market:
    def __init__(self):
        self.assets = [ # TODO: Add json parsing here
            Asset("Helios Corp.", 8000, -0.02, -0.001), # TODO: Trend should be random maybe?
            Asset("MacroHard", 1111, 0.0, -0.0005),
            Asset("Michaelsoft Binbows", 2422, 0.0, -0.1),
            Asset("Ionic Compound Manufacturers", 3500, 0.0, 0.0),
            Asset("ClosedAI", 10000, -0.3, -1),
            Asset("Photonic Semiconductors Limited", 4200, 0.06, -0.002),
            Asset("Super Earth Warbonds", 6969, -0.04, -0.003),
            Asset("Lithium Mining Associates", 5000, 0.2, -0.09),
            Asset("Tux", 10, 0.0, 0.5),
            Asset("Richard Bored Private Reserve", 1000, -0.1, 0.0),
            Asset("FICSIT, INC.", 4242, 0.1, -0.1)
        ]
        self.cycle = 0
        self.total_initial = sum(a.price for a in self.assets)
    
    def target_stability(self):
        t = self.cycle / CYCLES_TOTAL
        return max(0.0, 1 - math.log10(1 + 9 * t)) # also AI generated i hate math and knew i wanted something log
    
    def tick(self):
        stability = self.target_stability()
        
        for a in self.assets:
            a.update(stability)
        
        total = sum(a.price for a in self.assets)
        target = self.total_initial * stability
        if False:
            scale = target / total
            for a in self.assets:
                a.price *= scale
        self.total = total
        
        self.cycle += 1
        
    def summary(self):
        stability = self.target_stability()
        print(format_text(f"\n[Market Stability: {stability * 100:5.1f}%]   [Cycle {self.cycle}]\n", ["bright_cyan"]))
        print("total: ", self.total)
        
        for a in self.assets:
            col = "red" if a.delisted else "bright_green" if a.last_change > 0 else "bright_red" if a.last_change < 0 else "yellow"
            sym = "╳" if a.delisted else "⌃" if a.last_change > 0 else "⌄" if a.last_change < 0 else "~"
            if a.delisted:
                price = "[BKRP]"
            else:
                price = f"{a.price:8.2f}"
            if a.last_change > 0:
                last_change = f"+{a.last_change:.2f}"
            else:
                last_change = f"{a.last_change:8.2f}"
            print(f"{a.name:32} | {format_text(f"{sym} {last_change:>8}", [col])}", format_text(f"(Ⱡ{price})", [col]), sparkline(a.history, width = 10))
        
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
        clear()
        market.tick()
        market.summary()
        time.sleep(0.2)
    
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(format_text("test", ["bold", (False, 255, 80, 80), "bold", "underline"]))