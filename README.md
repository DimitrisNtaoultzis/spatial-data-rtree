# R-tree Spatial Index with STR Bulk Loading

Implementation of an R-tree spatial index using the Sort-Tile-Recursive (STR) bulk loading algorithm, with support for three types of spatial queries. Built as part of a Complex Data Management course assignment using a dataset of 51,970 restaurant locations in Beijing.

---

## Project Structure

```
├── rtree_build.py      # Part 1: Build R-tree using STR bulk loading
├── rtree_query.py      # Part 2: Spatial query algorithms
└── README.md
```

---

## Part 1 – Building the R-tree (`rtree_build.py`)

Constructs an R-tree in memory from a point dataset using STR bulk loading.

### How it works

**STR (Sort-Tile-Recursive)** is applied at the leaf level:
1. Sort all points by x-coordinate
2. Divide into vertical slabs
3. Within each slab, sort by y-coordinate and pack into leaf nodes
4. Build internal levels using traditional bulk loading (no sorting)

### Node capacities

| Node Type | Max Capacity | Min Capacity |
|-----------|-------------|-------------|
| Leaf      | M_L = 51    | m_L = 20    |
| Internal  | M_Int = 28  | m_Int = 11  |

### Output

Prints tree statistics per level and writes the tree to a CSV file:

```
1020 nodes at level 0 with average MBR area 0.0
37 nodes at level 1 with average MBR area 0.014773812397702606
2 nodes at level 2 with average MBR area 0.1640782578990009
1 nodes at level 3 with average MBR area 0.3246387377100014
```

### Usage

```bash
python3 rtree_build.py <input_file> <output_file>
```

Example:
```bash
python3 rtree_build.py Beijing_restaurants.txt rtree.csv
```

### Input format

```
51970
39.856138 116.42394
39.813336 116.486149
...
```

### Output format (rtree.csv)

Nodes are stored bottom-up (leaves first, root last):
```
0 , 51 , 0 , (42474,(39.74118, 116.070466)) , ...
1020 , 28 , 1 , (0,[39.682541, 116.070466, 39.74118, 116.119867]) , ...
```

Each line: `node-id , n , flag , (ptr1,geo1) , ...`
- `flag = 0`: leaf node — geometries are points `(x, y)`
- `flag = 1`: internal node — geometries are MBRs `[xlo, ylo, xhi, yhi]`

---

## Part 2 – Spatial Queries (`rtree_query.py`)

Loads the R-tree from `rtree.csv` and supports three query types.

### 1. Window Range Query

Finds all points inside a rectangular window W = (xlo, ylo, xhi, yhi).

Uses an iterative stack-based traversal:
- Internal node: visit child if its MBR overlaps W
- Leaf node: report point if it lies inside W

```bash
python3 rtree_query.py rtree.csv window windowRangeQueries.txt
```

Query file format: `xlo ylo xhi yhi` (one query per line)

Output:
```
0 (15): 20092,21791,17364,...
1 (48): 33905,37247,36551,...
```

---

### 2. Distance Range Query

Finds all points within Euclidean distance ε from a query point q.

Uses the same traversal as Window Range Query with different predicates:
- Internal node: visit child if `min_dist(q, MBR) ≤ ε`
- Leaf node: report point if `dist(q, p) ≤ ε`

```bash
python3 rtree_query.py rtree.csv distance distanceRangeQueries.txt
```

Query file format: `x y ε` (one query per line)

Output:
```
0 (62): 36666,10840,17494,...
1 (29): 8496,51939,5631,...
```

---

### 3. kNN Query (Best First Search)

Finds the k nearest neighbors of a query point q using a min-heap priority queue.

The priority queue stores both MBR entries and leaf points ordered by distance from q. When a point is popped from the queue, it is the next nearest neighbor.

```bash
python3 rtree_query.py rtree.csv knn NNQueries.txt <k>
```

Query file format: `x y` (one query per line)

Output (k=10):
```
0: 46099,8127,21812,41533,14833,1217,23761,27872,7544,43344
1: 7714,41566,10418,22944,38417,2038,27709,44845,16263,46309
```

---

## Requirements

No external libraries required. Only Python standard library modules are used:

- `sys`, `math`, `re`, `heapq`, `collections`

Tested with Python 3.8+.

---

## Dataset

The dataset (`Beijing_restaurants.txt`) contains 51,970 restaurant locations in Beijing and is **not included** in this repository. It can be obtained from the course page.
