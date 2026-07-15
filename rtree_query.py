#DIMITRIS NTAOULTZIS 5311
#PAVLOS MPASOUKEAS 5296

import sys
import math
import re
import heapq
from collections import defaultdict

ML       = 51
ML_MIN   = 20
MINT     = 28
MINT_MIN = 11


#Κλάση κόμβου
class Node:
    def __init__(self, node_id, is_leaf):
        self.node_id = node_id
        self.is_leaf = is_leaf
        self.entries = []

    def compute_mbr(self):
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


#Ανάγνωση rtree.csv
def load_rtree(filename):
    all_nodes = []
    with open(filename, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            # Χωρίζουμε τα πρώτα 3 πεδία: node-id, n, f
            # και μετά τις εγγραφές
            # Παράδειγμα γραμμής φύλλου:
            #   0 , 51 , 0 , (42474,(39.74118, 116.070466)) , ...
            # Παράδειγμα γραμμής ενδιάμεσου:
            #   1020 , 28 , 1 , (0,[39.68, 116.07, 39.74, 116.11]) , ...

            # Βρίσκουμε node_id, n, flag
            header = re.match(r'(\d+)\s*,\s*(\d+)\s*,\s*([01])\s*,\s*(.*)', line)
            node_id = int(header.group(1))
            n       = int(header.group(2))
            flag    = int(header.group(3))
            rest    = header.group(4)

            is_leaf = (flag == 0)
            node = Node(node_id, is_leaf)

            if is_leaf:
                # Βρίσκουμε εγγραφές τύπου (rec_id,(x, y))
                entries = re.findall(
                    r'\((\d+),\(([\d.]+),\s*([\d.]+)\)\)', rest
                )
                for (rec_id, x, y) in entries:
                    node.entries.append((int(rec_id), (float(x), float(y))))
            else:
                # Βρίσκουμε εγγραφές τύπου (node_id,[xlo, ylo, xhi, yhi])
                entries = re.findall(
                    r'\((\d+),\[([\d.]+),\s*([\d.]+),\s*([\d.]+),\s*([\d.]+)\]\)',
                    rest
                )
                for (nid, xlo, ylo, xhi, yhi) in entries:
                    node.entries.append((
                        int(nid),
                        (float(xlo), float(ylo), float(xhi), float(yhi))
                    ))

            all_nodes.append(node)

    return all_nodes



# ── Window Range Query ────────────────────────────────────

def mbr_overlaps_window(mbr, w):
    """
    Ελέγχει αν ένα MBR επικαλύπτεται με το παράθυρο W.
    mbr = (xlo, ylo, xhi, yhi)
    w   = (xlo, ylo, xhi, yhi)
    """
    # Δεν επικαλύπτονται αν το ένα είναι τελείως αριστερά,
    # δεξιά, πάνω ή κάτω από το άλλο
    if mbr[2] < w[0] or mbr[0] > w[2]:  # x άξονας
        return False
    if mbr[3] < w[1] or mbr[1] > w[3]:  # y άξονας
        return False
    return True


def point_in_window(point, w):
    """
    Ελέγχει αν ένα σημείο βρίσκεται εντός του παραθύρου W.
    point = (x, y)
    w     = (xlo, ylo, xhi, yhi)
    """
    return (w[0] <= point[0] <= w[2] and
            w[1] <= point[1] <= w[3])


def window_range_query(all_nodes, root_id, w):
    """
    Επιστρέφει λίστα από record-ids που βρίσκονται εντός του W.
    Χρησιμοποιεί στοίβα (iterative) αντί για αναδρομή.
    """
    results = []
    # Στοίβα με node-ids προς εξέταση — ξεκινάμε από τη ρίζα
    stack = [root_id]

    while stack:
        node_id = stack.pop()
        node = all_nodes[node_id]

        if node.is_leaf:
            # Ελέγχουμε κάθε σημείο
            for (rec_id, point) in node.entries:
                if point_in_window(point, w):
                    results.append(rec_id)
        else:
            # Ελέγχουμε κάθε MBR παιδιού
            for (child_id, mbr) in node.entries:
                if mbr_overlaps_window(mbr, w):
                    stack.append(child_id)

    return results


def run_window_queries(all_nodes, root_id, query_file):
    with open(query_file, 'r') as f:
        for i, line in enumerate(f):
            vals = list(map(float, line.strip().split()))
            w = (vals[0], vals[1], vals[2], vals[3])
            results = window_range_query(all_nodes, root_id, w)
            ids_str = ','.join(map(str, results))
            print(f"{i} ({len(results)}): {ids_str}")



# ── Distance Range Query ──────────────────────────────────

def min_dist_point_to_mbr(q, mbr):
    """
    Υπολογίζει την ελάχιστη απόσταση ενός σημείου q από ένα MBR.
    Αν το q είναι εντός του MBR, η απόσταση είναι 0.
    q   = (x, y)
    mbr = (xlo, ylo, xhi, yhi)
    """
    # Για κάθε διάσταση βρίσκουμε το κοντινότερο σημείο του MBR
    dx = max(mbr[0] - q[0], 0, q[0] - mbr[2])
    dy = max(mbr[1] - q[1], 0, q[1] - mbr[3])
    return math.sqrt(dx*dx + dy*dy)


def euclidean_dist(p1, p2):
    """Ευκλείδεια απόσταση μεταξύ δύο σημείων."""
    dx = p1[0] - p2[0]
    dy = p1[1] - p2[1]
    return math.sqrt(dx*dx + dy*dy)


def distance_range_query(all_nodes, root_id, q, epsilon):
    """
    Επιστρέφει λίστα από record-ids με απόσταση ≤ epsilon από το q.
    """
    results = []
    stack = [root_id]

    while stack:
        node_id = stack.pop()
        node = all_nodes[node_id]

        if node.is_leaf:
            for (rec_id, point) in node.entries:
                if euclidean_dist(q, point) <= epsilon:
                    results.append(rec_id)
        else:
            for (child_id, mbr) in node.entries:
                if min_dist_point_to_mbr(q, mbr) <= epsilon:
                    stack.append(child_id)

    return results


def run_distance_queries(all_nodes, root_id, query_file):
    with open(query_file, 'r') as f:
        for i, line in enumerate(f):
            vals = list(map(float, line.strip().split()))
            q       = (vals[0], vals[1])
            epsilon = vals[2]
            results = distance_range_query(all_nodes, root_id, q, epsilon)
            ids_str = ','.join(map(str, results))
            print(f"{i} ({len(results)}): {ids_str}")



# ── kNN Query (Best First Search) ─────────────────────────

def knn_query(all_nodes, root_id, q, k):
    """
    Επιστρέφει λίστα με τα k πλησιέστερα record-ids στο q.
    Χρησιμοποιεί min-heap για best-first search.
    Κάθε στοιχείο της ουράς: (απόσταση, τύπος, id)
    τύπος: 0 = κόμβος (MBR), 1 = σημείο (φύλλο)
    """
    # (dist, type, id)
    # type=0: node, type=1: point (record)
    heap = []
    heapq.heappush(heap, (0.0, 0, root_id))

    results = []  # (dist, rec_id)

    while heap and len(results) < k:
        dist, entry_type, entry_id = heapq.heappop(heap)

        if entry_type == 1:
            # Είναι σημείο — είναι ο επόμενος NN
            results.append(entry_id)
        else:
            # Είναι κόμβος — επεκτείνουμε τις εγγραφές του
            node = all_nodes[entry_id]
            if node.is_leaf:
                for (rec_id, point) in node.entries:
                    d = euclidean_dist(q, point)
                    heapq.heappush(heap, (d, 1, rec_id))
            else:
                for (child_id, mbr) in node.entries:
                    d = min_dist_point_to_mbr(q, mbr)
                    heapq.heappush(heap, (d, 0, child_id))

    return [rec_id for rec_id in results]


def run_knn_queries(all_nodes, root_id, query_file, k):
    with open(query_file, 'r') as f:
        for i, line in enumerate(f):
            vals = list(map(float, line.strip().split()))
            q = (vals[0], vals[1])
            results = knn_query(all_nodes, root_id, q, k)
            ids_str = ','.join(map(str, results))
            print(f"{i}: {ids_str}")



def main():
    if len(sys.argv) < 4:
        print("Usage: python part2.py <rtree.csv> <query_type> <query_file> [k]")
        print("  query_type: window | distance | knn")
        sys.exit(1)

    rtree_file = sys.argv[1]
    query_type = sys.argv[2]
    query_file = sys.argv[3]

    all_nodes = load_rtree(rtree_file)
    root_id = all_nodes[-1].node_id
    print(f"Loaded {len(all_nodes)} nodes")

    if query_type == "window":
        run_window_queries(all_nodes, root_id, query_file)
    elif query_type == "distance":
        run_distance_queries(all_nodes, root_id, query_file)
    elif query_type == "knn":
        if len(sys.argv) < 5:
            print("Requires k")
            sys.exit(1)
        k = int(sys.argv[4])
        run_knn_queries(all_nodes, root_id, query_file, k)
    else:
        print(f"Unknown query type: {query_type}")
        sys.exit(1)


if __name__ == "__main__":
    main()