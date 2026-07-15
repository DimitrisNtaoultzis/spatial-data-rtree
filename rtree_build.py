# DIMITRIS NTAOULTZIS 5311
# PAVLOS MPASOUKEAS 5296

import sys
import math


ML = 51  # μέγιστες εγγραφές φύλλου
ML_MIN = 20  # ελάχιστες εγγραφές φύλλου  (floor(0.4 * 51))
MINT = 28  # μέγιστες εγγραφές ενδιάμεσου
MINT_MIN = 11  # ελάχιστες εγγραφές ενδιάμεσου (floor(0.4 * 28))


# Κλάση κόμβου
class Node:
    def __init__(self, node_id, is_leaf):
        self.node_id = node_id
        self.is_leaf = is_leaf
        self.entries = []  # λίστα από (ptr, geo)

    def compute_mbr(self):
        """Υπολογίζει το MBR του κόμβου από τις εγγραφές του."""
        if self.is_leaf:
            xs = [e[1][0] for e in self.entries]
            ys = [e[1][1] for e in self.entries]
            return (min(xs), min(ys), max(xs), max(ys))
        else:
            xs_lo = [e[1][0] for e in self.entries]
            ys_lo = [e[1][1] for e in self.entries]
            xs_hi = [e[1][2] for e in self.entries]
            ys_hi = [e[1][3] for e in self.entries]
            return (min(xs_lo), min(ys_lo), max(xs_hi), max(ys_hi))


# Ανάγνωση αρχείου
def load_points(filename):
    points = []  # λίστα από (record_id, x, y)
    with open(filename, "r") as f:
        n = int(f.readline().strip())
        for i, line in enumerate(f, start=1):
            x, y = map(float, line.strip().split())
            points.append((i, x, y))
    return points


def build_leaf_level(points):
    """
    Εφαρμόζει STR για να φτιάξει το επίπεδο των φύλλων.
    Επιστρέφει λίστα από Node αντικείμενα.
    """
    N = len(points)
    num_leaves = math.ceil(N / ML)
    num_slabs = math.ceil(math.sqrt(num_leaves))

    # Βήμα 1: ταξινόμηση κατά x
    sorted_points = sorted(points, key=lambda p: p[1])

    # Βήμα 2: χωρισμός σε slabs
    slab_size = num_slabs * ML  # πόσα σημεία χωράει κάθε slab
    slabs = []
    for i in range(0, N, slab_size):
        slabs.append(sorted_points[i : i + slab_size])

    # Βήμα 3: μέσα σε κάθε slab ταξινόμηση κατά y και δημιουργία φύλλων
    leaf_groups = []  # κάθε group = λίστα σημείων για ένα φύλλο
    for slab in slabs:
        slab_sorted = sorted(slab, key=lambda p: p[2])
        for i in range(0, len(slab_sorted), ML):
            leaf_groups.append(slab_sorted[i : i + ML])

    # Βήμα 4: διόρθωση τελευταίου φύλλου αν έχει < ML_MIN εγγραφές
    if len(leaf_groups) > 1 and len(leaf_groups[-1]) < ML_MIN:
        prev = leaf_groups[-2]
        last = leaf_groups[-1]
        needed = ML_MIN - len(last)
        # παίρνουμε "needed" σημεία από το τέλος του προηγούμενου
        leaf_groups[-2] = prev[: len(prev) - needed]
        leaf_groups[-1] = prev[len(prev) - needed :] + last

    # Βήμα 5: δημιουργία Node αντικειμένων
    nodes = []
    for group in leaf_groups:
        node = Node(node_id=len(nodes), is_leaf=True)
        for rec_id, x, y in group:
            node.entries.append((rec_id, (x, y)))
        nodes.append(node)

    return nodes


def build_internal_level(child_nodes, all_nodes):
    N = len(child_nodes)

    # Χωρίζουμε τα παιδιά σε ομάδες των MINT με τη σειρά που έρχονται
    parent_groups = []
    for i in range(0, N, MINT):
        parent_groups.append(child_nodes[i : i + MINT])

    # Διόρθωση τελευταίου κόμβου αν έχει < MINT_MIN εγγραφές
    if len(parent_groups) > 1 and len(parent_groups[-1]) < MINT_MIN:
        prev = parent_groups[-2]
        last = parent_groups[-1]
        needed = MINT_MIN - len(last)
        parent_groups[-2] = prev[: len(prev) - needed]
        parent_groups[-1] = prev[len(prev) - needed :] + last

    # Δημιουργία Node αντικειμένων
    new_nodes = []
    for group in parent_groups:
        node = Node(node_id=len(all_nodes), is_leaf=False)
        for child in group:
            mbr = child.compute_mbr()
            node.entries.append((child.node_id, mbr))
        all_nodes.append(node)
        new_nodes.append(node)

    return new_nodes


def build_rtree(points):
    """
    Κατασκευάζει ολόκληρο το R-tree με STR bulk loading.
    Επιστρέφει τη λίστα all_nodes όπου all_nodes[i].node_id == i.
    """
    all_nodes = []

    # Επίπεδο φύλλων
    leaf_nodes = build_leaf_level(points)
    all_nodes.extend(leaf_nodes)

    # Ενδιάμεσα επίπεδα — συνεχίζουμε μέχρι να μείνει 1 κόμβος
    current_level = leaf_nodes
    while len(current_level) > 1:
        current_level = build_internal_level(current_level, all_nodes)

    # Ο τελευταίος κόμβος στο all_nodes είναι η ρίζα
    return all_nodes


def compute_mbr_area(mbr):
    """Υπολογίζει το εμβαδό ενός MBR."""
    return (mbr[2] - mbr[0]) * (mbr[3] - mbr[1])


def print_statistics(all_nodes):
    """
    Εκτυπώνει στατιστικά ανά επίπεδο.
    Επίπεδο 0 = φύλλα, επίπεδο 1 = πρώτο ενδιάμεσο, κλπ.
    """
    # Βρίσκουμε σε ποιο επίπεδο ανήκει κάθε κόμβος
    # Ξεκινάμε από τη ρίζα και κατεβαίνουμε
    levels = {}  # node_id -> level (μετράμε από φύλλα = 0)

    # Βρίσκουμε το ύψος του δέντρου μετρώντας από τη ρίζα
    root = all_nodes[-1]

    def assign_levels(node, level):
        levels[node.node_id] = level
        if not node.is_leaf:
            for child_id, _ in node.entries:
                assign_levels(all_nodes[child_id], level - 1)

    # Η ρίζα έχει το μέγιστο επίπεδο
    max_level = 0
    temp = root
    while not temp.is_leaf:
        max_level += 1
        temp = all_nodes[temp.entries[0][0]]

    assign_levels(root, max_level)

    # Ομαδοποίηση κόμβων ανά επίπεδο
    from collections import defaultdict

    level_nodes = defaultdict(list)
    for node in all_nodes:
        level_nodes[levels[node.node_id]].append(node)

    # Εκτύπωση
    for lv in sorted(level_nodes.keys()):
        nodes_at_level = level_nodes[lv]
        count = len(nodes_at_level)
        if lv == 0:
            avg_area = 0.0
        else:
            areas = [compute_mbr_area(n.compute_mbr()) for n in nodes_at_level]
            avg_area = sum(areas) / len(areas)
        print(f"{count} nodes at level {lv} with average MBR area {avg_area}")


def write_csv(all_nodes, output_file):
    """
    Γράφει το rtree.csv σε bottom-up σειρά
    """
    with open(output_file, "w") as f:
        for node in all_nodes:
            parts = []
            parts.append(str(node.node_id))
            parts.append(str(len(node.entries)))
            parts.append("0" if node.is_leaf else "1")

            for ptr, geo in node.entries:
                if node.is_leaf:
                    # σημείο: (record_id,(x, y))
                    geo_str = f"{geo[0]}, {geo[1]}"
                    parts.append(f"({ptr},({geo_str}))")
                else:
                    # MBR: (node_id,[xlo, ylo, xhi, yhi])
                    geo_str = f"{geo[0]}, {geo[1]}, {geo[2]}, {geo[3]}"
                    parts.append(f"({ptr},[{geo_str}])")

            f.write(" , ".join(parts) + "\n")


def main():
    if len(sys.argv) < 3:
        print("Usage: python part1.py <input_file> <output_file>\n")
        print("Example: python part1.py Beijing_restaurants.txt rtree.csv")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]

    points = load_points(input_file)
    print(f"Loaded {len(points)} points")

    print("Building R-tree with STR")
    all_nodes = build_rtree(points)
    print(f"Tree has {len(all_nodes)} nodes")

    print("\nTree statistics:")
    print_statistics(all_nodes)

    print(f"\nWriting file {output_file}...")
    write_csv(all_nodes, output_file)


if __name__ == "__main__":
    main()
