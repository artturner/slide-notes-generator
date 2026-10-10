import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import numpy as np

# Configuration for the PDF
filename = "AP_PreCalc_FRQ3_Practice_Set.pdf"

# Data for the 5 Questions
questions = [
    {
        "title": "Practice Question 1: The Ferris Wheel",
        "context": (
            "The 'Sky Eye' Ferris wheel is rotating at a constant speed. At time t=0 minutes, a rider boards a \n"
            "passenger car at the bottom of the wheel, which is 10 feet above the ground (h(0)=10). \n"
            "As the wheel turns, the rider reaches a maximum height of 110 feet above the ground. \n"
            "The wheel completes 3 full revolutions in 45 minutes. The sinusoidal function h models the \n"
            "rider's height above the ground in feet as a function of time t in minutes, for 0 <= t <= 45."
        ),
        # Wave Parameters for Graphing (Normalized for the generic view)
        # We want F to be the first Max. 
        # Scenario: Starts at Min (t=0). Period=15. 
        # Pattern: Min -> Mid -> Max (F) -> Mid (G) -> Min (J) -> Mid (K) -> Max (P)
        "graph_start_t": 5, # Start visualization slightly before F
        "graph_end_t": 25,
        "points": {
            "F": (7.5, 110),
            "G": (11.25, 60),
            "J": (15, 10),
            "K": (18.75, 60),
            "P": (22.5, 110)
        },
        "midline": 60,
        "amplitude": 50,
        "period": 15,
        "shift": -7.5, # Cosine peak at 7.5
        "solutions": {
            "A": "F(7.5, 110), G(11.25, 60), J(15, 10), K(18.75, 60), P(22.5, 110)",
            "B": "a=50, b=2π/15, c=-7.5, d=60",
            "C_i": "b. h is positive and decreasing.",
            "C_ii": "On (t1, t2), h is concave up. Rate of change is increasing."
        }
    },
    {
        "title": "Practice Question 2: The Tides",
        "context": (
            "A pier piling in a harbor is partially submerged in water. The depth of the water varies with the tides. \n"
            "At t=0 hours, it is high tide, and the water depth is 18 feet (h(0)=18). The depth decreases until \n"
            "it reaches low tide at t=6 hours, where the depth is 6 feet. The cycle repeats continuously. \n"
            "The sinusoidal function h models the water depth in feet as a function of time t in hours."
        ),
        # Scenario: Starts at Max (t=0). Period=12.
        # Pattern: Max (F) -> Mid (G) -> Min (J) -> Mid (K) -> Max (P)
        "graph_start_t": -1, 
        "graph_end_t": 13,
        "points": {
            "F": (0, 18),
            "G": (3, 12),
            "J": (6, 6),
            "K": (9, 12),
            "P": (12, 18)
        },
        "midline": 12,
        "amplitude": 6,
        "period": 12,
        "shift": 0, # Cosine peak at 0
        "solutions": {
            "A": "F(0, 18), G(3, 12), J(6, 6), K(9, 12), P(12, 18)",
            "B": "a=6, b=π/6, c=0 (or -12), d=12",
            "C_i": "a. h is positive and increasing.",
            "C_ii": "On (t1, t2), h is concave up. Rate of change is increasing."
        }
    },
    {
        "title": "Practice Question 3: The Pendulum",
        "context": (
            "A hypnosis pendulum swings back and forth. The horizontal distance from the center is modeled by h(t). \n"
            "At t=0, the bob is at its furthest point to the right, 8 cm from the center (h(0)=8). It swings to the left, \n"
            "reaching -8 cm, and then returns. It completes 5 full swings in 10 seconds. The sinusoidal function h \n"
            "models the signed distance in cm as a function of time t in seconds."
        ),
        # Scenario: Starts Max (t=0). Period = 10/5 = 2.
        # Pattern: Max (F) -> Mid (G) -> Min (J) -> Mid (K) -> Max (P)
        "graph_start_t": -0.2,
        "graph_end_t": 2.2,
        "points": {
            "F": (0, 8),
            "G": (0.5, 0),
            "J": (1.0, -8),
            "K": (1.5, 0),
            "P": (2.0, 8)
        },
        "midline": 0,
        "amplitude": 8,
        "period": 2,
        "shift": 0,
        "solutions": {
            "A": "F(0, 8), G(0.5, 0), J(1.0, -8), K(1.5, 0), P(2.0, 8)",
            "B": "a=8, b=π, c=0, d=0",
            "C_i": "b. h is positive and decreasing.",
            "C_ii": "On (t1, t2), h is concave down. Rate of change is decreasing."
        }
    },
    {
        "title": "Practice Question 4: The Reptile Heater",
        "context": (
            "The temperature inside a reptile enclosure cycles. At t=0 hours (midnight), the heater turns on, \n"
            "starting from the average temperature of 80°F and rising. The temperature reaches a high of 95°F, \n"
            "then drops to a low of 65°F, and returns to average. This cycle repeats every 8 hours. \n"
            "The sinusoidal function h models the temperature in °F as a function of time t in hours."
        ),
        # Scenario: Starts Midline Rising (t=0). Period 8. 
        # Max is at t=2. 
        # Pattern: Max (F) -> Mid (G) -> Min (J) -> Mid (K) -> Max (P)
        "graph_start_t": 1, 
        "graph_end_t": 11,
        "points": {
            "F": (2, 95),
            "G": (4, 80),
            "J": (6, 65),
            "K": (8, 80),
            "P": (10, 95)
        },
        "midline": 80,
        "amplitude": 15,
        "period": 8,
        "shift": -2, # Cosine peak at 2
        "solutions": {
            "A": "F(2, 95), G(4, 80), J(6, 65), K(8, 80), P(10, 95)",
            "B": "a=15, b=π/4, c=0 (sine) or -2 (cosine), d=80",
            "C_i": "b. h is positive and decreasing.",
            "C_ii": "On (t1, t2), h is concave up. Rate of change is increasing."
        }
    },
    {
        "title": "Practice Question 5: The Ocean Buoy",
        "context": (
            "A weather buoy floats in the ocean. At t=0 seconds, the buoy is at its lowest point, \n"
            "3 feet below sea level (h(0)=-3). It rises to a maximum height of 3 feet above sea level, \n"
            "and then drops back down. The buoy completes a full cycle every 6 seconds. \n"
            "The sinusoidal function h models the signed distance from sea level as a function of time t."
        ),
        # Scenario: Starts Min (t=0). Period 6. Max at t=3.
        # Pattern: Max (F) -> Mid (G) -> Min (J) -> Mid (K) -> Max (P)
        "graph_start_t": 2, 
        "graph_end_t": 10,
        "points": {
            "F": (3, 3),
            "G": (4.5, 0),
            "J": (6, -3),
            "K": (7.5, 0),
            "P": (9, 3)
        },
        "midline": 0,
        "amplitude": 3,
        "period": 6,
        "shift": -3,
        "solutions": {
            "A": "F(3, 3), G(4.5, 0), J(6, -3), K(7.5, 0), P(9, 3)",
            "B": "a=3, b=π/3, c=-3, d=0",
            "C_i": "a. h is positive and increasing.",
            "C_ii": "On (t1, t2), h is concave down. Rate of change is decreasing."
        }
    }
]

def create_question_page(pdf, q_data):
    # Setup Figure
    fig = plt.figure(figsize=(8.5, 11))
    
    # Title
    plt.text(0.5, 0.95, q_data["title"], ha='center', va='top', fontsize=16, weight='bold')
    
    # Context Text
    plt.text(0.1, 0.90, q_data["context"], ha='left', va='top', fontsize=11, wrap=True)
    
    # Part A Text
    plt.text(0.1, 0.75, "(A) The graph of h and its dashed midline is shown below.\n      Determine possible coordinates (t, h(t)) for points F, G, J, K, and P.", 
             ha='left', va='top', fontsize=12, weight='bold')

    # --- GRAPH GENERATION ---
    # Create axes for graph in the middle of page
    ax = fig.add_axes([0.15, 0.45, 0.7, 0.25]) # [left, bottom, width, height]
    
    # Generate Sine Wave Data
    t = np.linspace(q_data["graph_start_t"], q_data["graph_end_t"], 400)
    # Using Cosine form: a * cos(b(t+c)) + d
    # b = 2pi / period. c = shift. 
    b = 2 * np.pi / q_data["period"]
    # Note: Shift in formula a*cos(b(t+c)) implies c is horizontal shift. 
    # If peak is at 'peak_t', then arg is 0. b(peak_t + c) = 0 => c = -peak_t.
    # q_data['shift'] is defined as -peak_t in my data setup above.
    y = q_data["amplitude"] * np.cos(b * (t + q_data["shift"])) + q_data["midline"]
    
    # Plot Wave
    ax.plot(t, y, 'k-', linewidth=2)
    
    # Plot Midline
    ax.axhline(q_data["midline"], color='k', linestyle='--', linewidth=1)
    
    # Plot Points
    pts = q_data["points"]
    for label, (px, py) in pts.items():
        ax.plot(px, py, 'ko', markersize=6)
        # Offset label slightly
        ax.text(px, py + (q_data["amplitude"]*0.15), f"{label}", ha='center', fontsize=12, weight='bold')
        
    # Remove Axes Spines and Ticks (as per AP style "No scale indicated")
    ax.set_xticks([])
    ax.set_yticks([])
    # Keep left and bottom spine visible as a bounding box or remove entirely? 
    # Source says "No axes are presented".
    ax.spines['top'].set_visible(True)
    ax.spines['right'].set_visible(True)
    ax.spines['bottom'].set_visible(True)
    ax.spines['left'].set_visible(True)
    
    # --- END GRAPH ---

    # Part B Text
    plt.text(0.1, 0.40, "(B) The function h can be written in the form h(t) = a cos(b(t+c)) + d.\n      Find values of constants a, b, c, and d.", 
             ha='left', va='top', fontsize=12, weight='bold')
    plt.text(0.15, 0.35, "a = ______   b = ______   c = ______   d = ______", fontsize=12)

    # Part C Text
    plt.text(0.1, 0.25, "(C) Refer to the graph of h in part (A). Let the t-coordinate of G be t1\n      and the t-coordinate of J be t2.", 
             ha='left', va='top', fontsize=12, weight='bold')
    
    part_c_text = (
        "(i) On the interval (t1, t2), which of the following is true about h?\n"
        "     a. h is positive and increasing.\n"
        "     b. h is positive and decreasing.\n"
        "     c. h is negative and increasing.\n"
        "     d. h is negative and decreasing.\n\n"
        "(ii) Describe how the rate of change of h is changing on the interval (t1, t2)."
    )
    plt.text(0.15, 0.18, part_c_text, ha='left', va='top', fontsize=11)

    # Remove main figure axes
    plt.axis('off')
    pdf.savefig(fig)
    plt.close()

def create_solution_page(pdf, q_data):
    fig = plt.figure(figsize=(8.5, 11))
    
    plt.text(0.5, 0.9, f"Solution: {q_data['title']}", ha='center', fontsize=16, weight='bold')
    
    # Solutions
    sol_text = (
        f"(A) Coordinates:\n"
        f"    {q_data['solutions']['A']}\n\n"
        f"--------------------------------------------------\n\n"
        f"(B) Constants:\n"
        f"    {q_data['solutions']['B']}\n\n"
        f"--------------------------------------------------\n\n"
        f"(C) Analysis:\n"
        f"    (i) {q_data['solutions']['C_i']}\n\n"
        f"    (ii) {q_data['solutions']['C_ii']}"
    )
    
    plt.text(0.1, 0.75, sol_text, ha='left', va='top', fontsize=12, wrap=True)
    
    plt.axis('off')
    pdf.savefig(fig)
    plt.close()

# Generate PDF
with PdfPages(filename) as pdf:
    for q in questions:
        create_question_page(pdf, q)
        create_solution_page(pdf, q)

print(f"PDF '{filename}' generated successfully.")