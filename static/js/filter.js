// Standalone Category Filter for Challenges
document.addEventListener('DOMContentLoaded', function () {
  const filterBtns = document.querySelectorAll('.filter-btn');
  const challengeCards = document.querySelectorAll('.challenge-card');

  if (filterBtns.length === 0 || challengeCards.length === 0) {
    return;
  }

  filterBtns.forEach(btn => {
    btn.addEventListener('click', function () {
      const selectedCategory = this.getAttribute('data-category');

      // Update active button
      filterBtns.forEach(b => b.classList.remove('active'));
      this.classList.add('active');

      // Filter cards
      challengeCards.forEach(card => {
        const cardCategory = card.getAttribute('data-category');

        if (selectedCategory === 'all' || cardCategory === selectedCategory) {
          card.classList.remove('hidden');
          card.style.display = '';
        } else {
          card.classList.add('hidden');
          card.style.display = 'none';
        }
      });
    });
  });
});
