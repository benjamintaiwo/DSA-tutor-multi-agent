import json
import random
import urllib.request
import urllib.error

class LeetCodeTool:
    """
    A tool to fetch LeetCode problems using the public GraphQL API.
    """

    def __init__(self):
        self.base_url = "https://leetcode.com/graphql"
        self.headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36"
        }

    def get_problem(self, slug: str) -> str:
        """
        Fetches a problem by its slug (e.g., 'two-sum') from LeetCode.
        """
        slug = slug.lower().strip()
        
        query = """
        query getQuestionDetail($titleSlug: String!) {
          question(titleSlug: $titleSlug) {
            questionId
            title
            difficulty
            content
            topicTags {
              name
            }
            codeSnippets {
              lang
              code
            }
            sampleTestCase
          }
        }
        """
        
        payload = {
            "query": query,
            "variables": {"titleSlug": slug}
        }
        
        try:
            req = urllib.request.Request(
                self.base_url, 
                data=json.dumps(payload).encode('utf-8'), 
                headers=self.headers, 
                method='POST'
            )
            
            with urllib.request.urlopen(req) as response:
                if response.getcode() == 200:
                    data = json.loads(response.read().decode('utf-8'))
                    question = data.get("data", {}).get("question")
                    
                    if not question:
                        return f"Error: Problem '{slug}' not found on LeetCode."
                        
                    # Clean up content (it's HTML) - for now just return as is or strip tags if needed
                    # The LLM can handle HTML usually.
                    
                    result = {
                        "title": question["title"],
                        "difficulty": question["difficulty"],
                        "category": [tag["name"] for tag in question.get("topicTags", [])],
                        "description": question["content"], # HTML content
                        "examples": question.get("sampleTestCase"), # Raw string
                        "constraints": "See description" # Often embedded in content
                    }
                    return json.dumps(result, indent=2)
                else:
                    return f"Error: Failed to fetch problem. Status code: {response.getcode()}"
                    
        except urllib.error.URLError as e:
            return f"Error: Network error fetching problem: {e}"
        except Exception as e:
            return f"Error: An unexpected error occurred: {e}"

    def get_random_problem(self) -> str:
        """
        Fetches a random problem. 
        Since we can't easily get a random slug without a list, 
        we'll pick from a curated list of popular interview questions.
        """
        popular_slugs = [
            "two-sum", "add-two-numbers", "longest-substring-without-repeating-characters",
            "median-of-two-sorted-arrays", "longest-palindromic-substring", "zigzag-conversion",
            "reverse-integer", "string-to-integer-atoi", "palindrome-number", "regular-expression-matching",
            "container-with-most-water", "integer-to-roman", "roman-to-integer", "longest-common-prefix",
            "3sum", "3sum-closest", "letter-combinations-of-a-phone-number", "4sum",
            "remove-nth-node-from-end-of-list", "valid-parentheses", "merge-two-sorted-lists",
            "generate-parentheses", "merge-k-sorted-lists", "swap-nodes-in-pairs", "reverse-nodes-in-k-group",
            "remove-duplicates-from-sorted-array", "remove-element", "implement-strstr", "divide-two-integers",
            "substring-with-concatenation-of-all-words", "next-permutation", "longest-valid-parentheses",
            "search-in-rotated-sorted-array", "find-first-and-last-position-of-element-in-sorted-array",
            "search-insert-position", "valid-sudoku", "sudoku-solver", "count-and-say",
            "combination-sum", "combination-sum-ii", "first-missing-positive", "trapping-rain-water",
            "multiply-strings", "wildcard-matching", "jump-game-ii", "permutations", "permutations-ii",
            "rotate-image", "group-anagrams", "powx-n", "n-queens", "n-queens-ii", "maximum-subarray",
            "spiral-matrix", "jump-game", "merge-intervals", "insert-interval", "length-of-last-word",
            "spiral-matrix-ii", "permutation-sequence", "rotate-list", "unique-paths", "unique-paths-ii",
            "minimum-path-sum", "valid-number", "plus-one", "add-binary", "text-justification", "sqrtx",
            "climbing-stairs", "simplify-path", "edit-distance", "set-matrix-zeroes", "search-a-2d-matrix",
            "sort-colors", "minimum-window-substring", "combinations", "subsets", "word-search",
            "remove-duplicates-from-sorted-array-ii", "search-in-rotated-sorted-array-ii",
            "remove-duplicates-from-sorted-list-ii", "remove-duplicates-from-sorted-list",
            "largest-rectangle-in-histogram", "maximal-rectangle", "partition-list", "scramble-string",
            "merge-sorted-array", "gray-code", "subsets-ii", "decode-ways", "reverse-linked-list-ii",
            "restore-ip-addresses", "binary-tree-inorder-traversal", "unique-binary-search-trees-ii",
            "unique-binary-search-trees", "interleaving-string", "validate-binary-search-tree",
            "recover-binary-search-tree", "same-tree", "symmetric-tree", "binary-tree-level-order-traversal",
            "zigzag-level-order-traversal", "maximum-depth-of-binary-tree", "construct-binary-tree-from-preorder-and-inorder-traversal",
            "construct-binary-tree-from-inorder-and-postorder-traversal", "binary-tree-level-order-traversal-ii",
            "convert-sorted-array-to-binary-search-tree", "convert-sorted-list-to-binary-search-tree",
            "balanced-binary-tree", "minimum-depth-of-binary-tree", "path-sum", "path-sum-ii",
            "flatten-binary-tree-to-linked-list", "distinct-subsequences", "populating-next-right-pointers-in-each-node",
            "populating-next-right-pointers-in-each-node-ii", "pascals-triangle", "pascals-triangle-ii",
            "triangle", "best-time-to-buy-and-sell-stock", "best-time-to-buy-and-sell-stock-ii",
            "best-time-to-buy-and-sell-stock-iii", "binary-tree-maximum-path-sum", "valid-palindrome",
            "word-ladder", "word-ladder-ii", "longest-consecutive-sequence", "sum-root-to-leaf-numbers",
            "surrounded-regions", "palindrome-partitioning", "palindrome-partitioning-ii", "clone-graph",
            "gas-station", "candy", "single-number", "single-number-ii", "copy-list-with-random-pointer",
            "word-break", "word-break-ii", "linked-list-cycle", "linked-list-cycle-ii", "reorder-list",
            "binary-tree-preorder-traversal", "binary-tree-postorder-traversal", "lru-cache",
            "insertion-sort-list", "sort-list", "max-points-on-a-line", "evaluate-reverse-polish-notation",
            "reverse-words-in-a-string", "maximum-product-subarray", "find-minimum-in-rotated-sorted-array",
            "find-minimum-in-rotated-sorted-array-ii", "min-stack", "binary-tree-upside-down",
            "read-n-characters-given-read4", "read-n-characters-given-read4-ii-call-multiple-times",
            "longest-substring-with-at-most-two-distinct-characters", "intersection-of-two-linked-lists",
            "one-edit-distance", "find-peak-element", "missing-ranges", "maximum-gap", "compare-version-numbers",
            "fraction-to-recurring-decimal", "two-sum-ii-input-array-is-sorted", "excel-sheet-column-title",
            "majority-element", "two-sum-iii-data-structure-design", "excel-sheet-column-number",
            "factorial-trailing-zeroes", "binary-search-tree-iterator", "dungeon-game", "largest-number",
            "repeated-dna-sequences", "best-time-to-buy-and-sell-stock-iv", "rotate-array", "reverse-bits",
            "number-of-1-bits", "house-robber", "binary-tree-right-side-view", "number-of-islands",
            "bitwise-and-of-numbers-range", "happy-number", "remove-linked-list-elements", "count-primes",
            "isomorphic-strings", "reverse-linked-list", "course-schedule", "implement-trie-prefix-tree",
            "minimum-size-subarray-sum", "course-schedule-ii", "add-and-search-word-data-structure-design",
            "word-search-ii", "house-robber-ii", "shortest-palindrome", "kth-largest-element-in-an-array",
            "combination-sum-iii", "contains-duplicate", "the-skyline-problem", "contains-duplicate-ii",
            "contains-duplicate-iii", "maximal-square", "count-complete-tree-nodes", "rectangle-area",
            "basic-calculator", "implement-stack-using-queues", "invert-binary-tree", "basic-calculator-ii",
            "summary-ranges", "majority-element-ii", "kth-smallest-element-in-a-bst", "power-of-two",
            "implement-queue-using-stacks", "number-of-digit-one", "palindrome-linked-list",
            "lowest-common-ancestor-of-a-binary-search-tree", "lowest-common-ancestor-of-a-binary-tree",
            "delete-node-in-a-linked-list", "product-of-array-except-self", "sliding-window-maximum",
            "search-a-2d-matrix-ii", "different-ways-to-add-parentheses", "valid-anagram", "shortest-word-distance",
            "shortest-word-distance-ii", "shortest-word-distance-iii", "strobogrammatic-number",
            "strobogrammatic-number-ii", "strobogrammatic-number-iii", "group-shifted-strings", "count-univalue-subtrees",
            "flatten-2d-vector", "meeting-rooms", "meeting-rooms-ii", "factor-combinations", "verify-preorder-sequence-in-binary-search-tree",
            "paint-house", "binary-tree-paths", "add-digits", "3sum-smaller", "single-number-iii", "graph-valid-tree",
            "ugly-number", "ugly-number-ii", "paint-house-ii", "palindrome-permutation", "palindrome-permutation-ii",
            "missing-number", "alien-dictionary", "closest-binary-search-tree-value", "encode-and-decode-strings",
            "closest-binary-search-tree-value-ii", "integer-to-english-words", "h-index", "h-index-ii", "paint-fence",
            "find-the-celebrity", "first-bad-version", "perfect-squares", "wiggle-sort", "zigzag-iterator",
            "expression-add-operators", "move-zeroes", "peeking-iterator", "inorder-successor-in-bst",
            "walls-and-gates", "find-the-duplicate-number", "unique-word-abbreviation", "game-of-life",
            "word-pattern", "word-pattern-ii", "nim-game", "flip-game", "flip-game-ii", "find-median-from-data-stream",
            "best-meeting-point", "serialize-and-deserialize-binary-tree", "binary-tree-longest-consecutive-sequence",
            "bulls-and-cows", "longest-increasing-subsequence", "remove-invalid-parentheses",
            "smallest-rectangle-enclosing-black-pixels", "range-sum-query-immutable", "range-sum-query-2d-immutable",
            "number-of-islands-ii", "additive-number", "range-sum-query-mutable", "range-sum-query-2d-mutable",
            "best-time-to-buy-and-sell-stock-with-cooldown", "minimum-height-trees", "burst-balloons",
            "super-ugly-number", "binary-tree-vertical-order-traversal", "count-of-smaller-numbers-after-self",
            "remove-duplicate-letters", "shortest-distance-from-all-buildings", "maximum-product-of-word-lengths",
            "bulb-switcher", "generalized-abbreviation", "create-maximum-number", "coin-change",
            "number-of-connected-components-in-an-undirected-graph", "wiggle-sort-ii", "maximum-size-subarray-sum-equals-k",
            "power-of-three", "count-of-range-sum", "odd-even-linked-list", "longest-increasing-path-in-a-matrix",
            "patching-array", "verify-preorder-serialization-of-a-binary-tree", "reconstruct-itinerary",
            "increasing-triplet-subsequence", "self-crossing", "palindrome-pairs", "house-robber-iii",
            "counting-bits", "nested-list-weight-sum", "longest-substring-with-at-most-k-distinct-characters",
            "flatten-nested-list-iterator", "power-of-four", "integer-break", "reverse-string", "reverse-vowels-of-a-string",
            "moving-average-from-data-stream", "top-k-frequent-elements", "design-tic-tac-toe", "intersection-of-two-arrays",
            "intersection-of-two-arrays-ii", "android-unlock-patterns", "data-stream-as-disjoint-intervals",
            "design-snake-game", "russian-doll-envelopes", "design-twitter", "line-reflection", "count-numbers-with-unique-digits",
            "rearrange-string-k-distance-apart", "logger-rate-limiter", "sort-transformed-array", "bomb-enemy",
            "design-hit-counter", "max-sum-of-rectangle-no-larger-than-k", "nested-list-weight-sum-ii",
            "water-and-jug-problem", "find-leaves-of-binary-tree", "valid-perfect-square", "largest-divisible-subset",
            "plus-one-linked-list", "range-addition", "sum-of-two-integers", "super-pow", "find-k-pairs-with-smallest-sums",
            "guess-number-higher-or-lower", "guess-number-higher-or-lower-ii", "wiggle-subsequence", "combination-sum-iv",
            "kth-smallest-element-in-a-sorted-matrix", "insert-delete-getrandom-o1", "insert-delete-getrandom-o1-duplicates-allowed",
            "linked-list-random-node", "ransom-note", "shuffle-an-array", "mini-parser", "lexicographical-numbers",
            "first-unique-character-in-a-string", "longest-absolute-file-path", "find-the-difference",
            "elimination-game", "perfect-rectangle", "is-subsequence", "utf-8-validation", "decode-string",
            "longest-substring-with-at-least-k-repeating-characters", "rotate-function", "integer-replacement",
            "random-pick-index", "evaluate-division", "nth-digit", "binary-watch", "remove-k-digits",
            "frog-jump", "sum-of-left-leaves", "convert-a-number-to-hexadecimal", "queue-reconstruction-by-height",
            "trapping-rain-water-ii", "pacific-atlantic-water-flow", "sentence-screen-fitting", "construct-quad-tree",
            "fizz-buzz", "arithmetic-slices", "third-maximum-number", "add-strings", "partition-equal-subset-sum",
            "pacific-atlantic-water-flow", "battleships-in-a-board", "strong-password-checker",
            "maximum-xor-of-two-numbers-in-an-array", "valid-word-abbreviation", "word-squares", "reconstruct-original-digits-from-english",
            "longest-repeating-character-replacement", "construct-binary-tree-from-string", "quad-tree-intersection",
            "sequence-reconstruction", "find-all-anagrams-in-a-string", "find-right-interval", "path-sum-iii",
            "find-all-numbers-disappeared-in-an-array", "number-of-boomerangs", "serialize-and-deserialize-bst",
            "delete-node-in-a-bst", "sort-characters-by-frequency", "minimum-number-of-arrows-to-burst-balloons",
            "minimum-moves-to-equal-array-elements", "4sum-ii", "assign-cookies", "132-pattern", "circular-array-loop",
            "poor-pigs", "repeated-substring-pattern", "lfu-cache", "hamming-distance", "minimum-moves-to-equal-array-elements-ii",
            "island-perimeter", "can-i-win", "count-the-repetitions", "unique-substrings-in-wraparound-string",
            "validate-ip-address", "convex-polygon", "concatenated-words", "matchsticks-to-square", "ones-and-zeroes",
            "heaters", "number-complement", "total-hamming-distance", "generate-random-point-in-a-circle",
            "largest-palindrome-product", "sliding-window-median", "magical-string", "license-key-formatting",
            "smallest-good-base", "max-consecutive-ones", "predict-the-winner", "ones-and-zeroes", "zuma-game",
            "increasing-subsequences", "construct-the-rectangle", "reverse-pairs", "target-sum", "teemo-attacking",
            "next-greater-element-i", "random-point-in-non-overlapping-rectangles", "diagonal-traverse",
            "keyboard-row", "find-mode-in-binary-search-tree", "ipo", "next-greater-element-ii", "base-7",
            "relative-ranks", "perfect-number", "most-frequent-subtree-sum", "fibonacci-number", "find-largest-value-in-each-tree-row",
            "freedom-trail", "find-bottom-left-tree-value", "longest-palindromic-subsequence", "super-washing-machines",
            "coin-change-2", "random-flip-matrix", "detect-capital", "longest-uncommon-subsequence-i",
            "longest-uncommon-subsequence-ii", "continuous-subarray-sum", "longest-word-in-dictionary-through-deleting",
            "contiguous-array", "beautiful-arrangement", "random-pick-with-weight", "minesweeper", "minimum-absolute-difference-in-bst",
            "lonely-pixel-i", "k-diff-pairs-in-an-array", "lonely-pixel-ii", "encode-and-decode-tinyurl",
            "construct-binary-tree-from-string", "complex-number-multiplication", "convert-bst-to-greater-tree",
            "minimum-time-difference", "single-element-in-a-sorted-array", "reverse-string-ii", "01-matrix",
            "diameter-of-binary-tree", "output-contest-matches", "boundary-of-binary-tree", "remove-boxes",
            "number-of-provinces", "student-attendance-record-i", "student-attendance-record-ii", "optimal-division",
            "brick-wall", "split-array-with-equal-sum", "next-greater-element-iii", "reverse-words-in-a-string-iii",
            "logical-or-of-two-binary-grids-represented-as-quad-trees", "maximum-depth-of-n-ary-tree",
            "subarray-sum-equals-k", "array-partition-i", "binary-tree-tilt", "find-the-closest-palindrome",
            "array-nesting", "reshape-the-matrix", "permutation-in-string", "maximum-vacation-days", "median-of-two-sorted-arrays"
        ]
        slug = random.choice(popular_slugs)
        return self.get_problem(slug)
