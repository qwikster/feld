import sys
import os
import time
import random
import math

# config
START_LUX = 10000
CYCLES_TOTAL = 50
TICK_RATE = 2.5

HAB_COST = 50000
SUPPLY_COST = 500
SUPPLY_START = 5
SUPPLY_CONS = 1

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

def glitch(text: str, intensity: float, glitch_characters: str = "#$@%&^/?X") -> str:
    # TODO: Add unicode? lookalike table?
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
    scaled = [(v - lo) / span for v in vals]
    idxs = [int(s * (len(GRAPH_CHARS) - 1)) for s in scaled]

    mid_val = sum(vals) / n
    mid_idx = int(((mid_val - lo) / span) * (len(GRAPH_CHARS) - 1))

    parts = []
    for i in range(n):
        if i == 0:
            delta = 0
        else:
            delta = vals[i] - vals[i - 1]
        if abs(delta) < 0.05:
            col = "bright_yellow"
        elif delta > 0:
            col = "bright_green"
        else:
            col = "bright_red"
        
        ch = GRAPH_CHARS[idxs[i]]
        parts.append(format_text(ch, [col]))

    return "".join(parts)

# classes
class Asset: # subclass to be used only under Market
    def __init__(self, name, base, volatility, resilience = 1.0):
        self.name = name
        self.price = base
        self.volatility = volatility # How much asset is allowed to fluctuate
        self.resilience = float(resilience) if resilience > 0 else 1.0 # how easily it will decay, commonness of bursts
        self.trend = random.uniform(-0.05, 0.05) # keeps believable strings of up and down
        self.last_change = 0.0  # For stock ticker
        self.history = [self.price]
        self.delisted = False
        self.t = 0
        
    def update(self, stability: float):
        self.t += 1
        prev = self.price

        if self.delisted:
            self.price = 0.0
            self.last_change = 0.0
            return

        trend_change = random.uniform(-0.02, 0.02)
        self.trend += trend_change

        decay_factor = (1.0 - stability) ** 2 # Add pressure to drop as stability drops
        if stability < 0.06:
            decay_factor = 69.420
        sensitivity = decay_factor * (0.4 / self.resilience) # Scale by asset resilience
        trend_force = self.trend * (0.6 + 0.4 * stability) # Trend up or down so it's not super random
        random_fluct = random.uniform(-self.volatility, self.volatility) # Standard fluctuations
        burst = 0.0 # occasional burst to keep it alive
        if random.random() < 0.1 and stability < 0.6:
            burst = random.uniform(0.01, 0.2) # 

        delta_pct = trend_force - sensitivity + random_fluct + burst
        
        self.decay_factor, self.sensitivity, self.trend_force, self.random_fluct, self.burst, self.delta_pct = decay_factor, sensitivity, trend_force, random_fluct, burst, delta_pct
        # for debug, never actually used
        
        self.price = max(0.0, self.price * (1.0 + delta_pct))
        self.last_change = self.price - prev
        self.history.append(self.price)
        
        if self.price <= 0.5:
            self.price = 0.0
            self.delisted = True

class Market:
    def __init__(self):
        self.assets = [ # TODO: Add json parsing here
            Asset("Helios Corp.", 8000, 0.02, 1.2), # name, base, volatility, resilience
            Asset("MacroHard", 1111, 0.015, 1.0),
            Asset("Michaelsoft Binbows", 2422, 0.01, 0.9),
            Asset("Ionic Compound Manufacturers", 3500, 0.012, 1.1),
            Asset("ClosedAI", 10000, 0.3, 0.3),
            Asset("Photonic Semiconductors Limited", 4200, 0.02, 1.0),
            Asset("Super Earth Warbonds", 6969, 0.04, 1.3),
            Asset("Lithium Mining Associates", 5000, 0.025, 0.9),
            Asset("Tux", 10, 0.1, 1.5),
            Asset("Richard Bored Private Reserve", 1000, 0.005, 1.2),
            Asset("FICSIT, INC.", 4242, 0.03, 1.15)
        ]
        self.cycle = 0
    
    def tick(self):
        stability = self.target_stability(self.cycle)

        for a in self.assets:
            a.update(stability)
        self.cycle += 1
        
    def target_stability(self, cycle):
       t = cycle / CYCLES_TOTAL
       stability = 1.0 - t ** 2.8
       return max(0.0, min(1.0, stability))

    def summary(self):
        stability = self.target_stability(self.cycle)
        print(format_text(f"\n[Market Stability: {stability * 100:5.1f}%]   [Cycle {self.cycle}]\n", ["bright_cyan"]))
        
        for a in self.assets:
            col = "red" if a.delisted else "bright_green" if a.last_change > 0 else "bright_red" if a.last_change < 0 else "yellow"
            sym = "╳" if a.delisted else "⌃" if a.last_change > 0 else "⌄" if a.last_change < 0 else "~"
            if a.delisted:
                price = " [BKRP] "
            else:
                price = f"{a.price:8.2f}"
            if a.last_change > 0:
                last_change = f"+{a.last_change:.2f}"
            else:
                last_change = f"{a.last_change:8.2f}"
            print(f"{a.name:32} | {format_text(f"{sym} {last_change:>8}", [col])}", format_text(f"(Ⱡ{price})", [col]), sparkline(a.history, width = 10))
            
            if False: # DEBUG
                print(
                    "trend: ", str(round(a.trend, 4)).ljust(10),
                    "    decay: ", str(round(a.decay_factor, 4)).ljust(10),
                    "\nsnsvy: ", str(round(a.sensitivity, 4)).ljust(10),
                    "    tfrce: ", str(round(a.trend_force, 4)).ljust(10),
                    "\nfluct: ", str(round(a.random_fluct, 4)).ljust(10),
                    "    burst: ", str(round(a.burst, 4)).ljust(10), "\n")
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
        input()
    
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(format_text("test", ["bold", (False, 255, 80, 80), "bold", "underline"]))