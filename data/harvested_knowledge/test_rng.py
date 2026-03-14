from krkn_ai.utils.rng import RNG


class TestRNG:
    def test_init_without_seed(self):
        """Test initialization without a seed."""
        rng = RNG()
        assert rng.get_seed() is None
        # Should produce a number
        assert 0.0 <= rng.random() < 1.0

    def test_init_with_seed(self):
        """Test initialization with a specific seed."""
        seed = 42
        rng = RNG(seed)
        assert rng.get_seed() == seed

        # Verify reproducibility
        val1 = rng.random()

        rng2 = RNG(seed)
        val2 = rng2.random()
        assert val1 == val2

    def test_set_seed(self):
        """Test setting the seed after initialization."""
        rng = RNG()
        seed = 12345
        rng.set_seed(seed)
        assert rng.get_seed() == seed

        val1 = rng.random()

        # Reset with same seed
        rng.set_seed(seed)
        val2 = rng.random()
        assert val1 == val2

    def test_random(self):
        """Test random() returns a float between 0.0 and 1.0."""
        rng = RNG(42)
        val = rng.random()
        assert isinstance(val, float)
        assert 0.0 <= val < 1.0

    def test_choice(self):
        """Test choice() picks an element from a sequence."""
        rng = RNG(42)
        items = [1, 2, 3, 4, 5]
        choice = rng.choice(items)
        assert choice in items

        # Reproducibility check
        rng.set_seed(42)
        choice2 = rng.choice(items)
        assert choice == choice2

    def test_choices(self):
        """Test choices() picks multiple elements with weights."""
        rng = RNG(42)
        items = ["a", "b", "c"]
        weights = [0.1, 0.8, 0.1]

        # "b" has highest weight, should appear most often in a large sample
        # but for a simple unit test we just check return structure
        choices = rng.choices(items, weights, k=5)
        assert len(choices) == 5
        assert all(c in items for c in choices)

        # Reproducibility check
        rng.set_seed(42)
        choices2 = rng.choices(items, weights, k=5)
        assert choices == choices2

    def test_randint(self):
        """Test randint() returns an integer within range."""
        rng = RNG(42)
        low, high = 1, 10
        val = rng.randint(low, high)
        assert isinstance(val, int)
        assert low <= val < high

        # Test low == high case
        assert rng.randint(5, 5) == 5

    def test_uniform(self):
        """Test uniform() returns a float within range."""
        rng = RNG(42)
        low, high = 1.5, 5.5
        val = rng.uniform(low, high)
        assert isinstance(val, float)
        assert low <= val <= high
