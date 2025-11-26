// Main JavaScript for CTF Platform

// CSRF Token helper
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

// Flag submission handler
function submitFlag(challengeId) {
  const flagInput = document.getElementById('flag-input');
  const submitBtn = document.getElementById('submit-btn');
  const resultDiv = document.getElementById('submission-result');

  if (!flagInput || !submitBtn) return;

  const flag = flagInput.value.trim();

  if (!flag) {
    showMessage('Please enter a flag', 'error');
    return;
  }

  // Disable button and show loading
  submitBtn.disabled = true;
  submitBtn.innerHTML = '<span class="loading"></span> Submitting...';

  // Submit flag via AJAX
  fetch(`/challenges/${challengeId}/submit/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCookie('csrftoken')
    },
    body: JSON.stringify({ flag: flag })
  })
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        showMessage(data.message, 'success');
        flagInput.disabled = true;
        submitBtn.style.display = 'none';

        // Show solved badge
        const solvedBadge = document.createElement('span');
        solvedBadge.className = 'solved-badge';
        solvedBadge.textContent = '✓ Solved';
        document.querySelector('.challenge-meta').appendChild(solvedBadge);

        // Update user score if displayed
        updateUserScore(data.points);
      } else {
        showMessage(data.message, 'error');
        submitBtn.disabled = false;
        submitBtn.innerHTML = 'Submit Flag';
      }
    })
    .catch(error => {
      console.error('Error:', error);
      showMessage('An error occurred. Please try again.', 'error');
      submitBtn.disabled = false;
      submitBtn.innerHTML = 'Submit Flag';
    });
}

// Show message helper
function showMessage(message, type) {
  const existingMessages = document.querySelector('.messages');
  if (existingMessages) {
    existingMessages.remove();
  }

  const messageDiv = document.createElement('div');
  messageDiv.className = 'messages';
  messageDiv.innerHTML = `<div class="alert alert-${type}">${message}</div>`;

  const mainContent = document.querySelector('.main-content');
  mainContent.insertBefore(messageDiv, mainContent.firstChild);

  // Auto-remove after 5 seconds
  setTimeout(() => {
    messageDiv.remove();
  }, 5000);
}

// Update user score in navigation
function updateUserScore(points) {
  // This would update any score display in the UI
  console.log(`User earned ${points} points!`);
}

// Live leaderboard updates
function updateLeaderboard() {
  const leaderboardTable = document.getElementById('leaderboard-table');
  if (!leaderboardTable) return;

  fetch('/leaderboard/api/')
    .then(response => response.json())
    .then(data => {
      const tbody = leaderboardTable.querySelector('tbody');
      if (!tbody) return;

      tbody.innerHTML = '';

      data.leaderboard.forEach(user => {
        const row = document.createElement('tr');
        if (user.rank <= 3) {
          row.className = `rank-${user.rank}`;
        }

        row.innerHTML = `
                <td>${user.rank}</td>
                <td>${user.username}</td>
                <td>${user.score}</td>
                <td>${user.challenges_solved}</td>
            `;

        tbody.appendChild(row);
      });
    })
    .catch(error => {
      console.error('Error updating leaderboard:', error);
    });
}

// CTF Timer functionality
function startCTFTimer(endTime) {
  const timerElement = document.getElementById('ctf-timer');
  if (!timerElement) return;

  function updateTimer() {
    const now = new Date().getTime();
    const distance = endTime - now;

    if (distance < 0) {
      timerElement.innerHTML = "CTF ENDED";
      return;
    }

    const days = Math.floor(distance / (1000 * 60 * 60 * 24));
    const hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
    const minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
    const seconds = Math.floor((distance % (1000 * 60)) / 1000);

    timerElement.innerHTML = `${days}d ${hours}h ${minutes}m ${seconds}s`;
  }

  updateTimer();
  setInterval(updateTimer, 1000);
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function () {
  // Auto-update leaderboard every 30 seconds if on leaderboard page
  if (document.getElementById('leaderboard-table')) {
    setInterval(updateLeaderboard, 30000);
  }

  // Initialize CTF timer if present
  const timerElement = document.getElementById('ctf-timer');
  if (timerElement && timerElement.dataset.endTime) {
    const endTime = new Date(timerElement.dataset.endTime).getTime();
    startCTFTimer(endTime);
  }

  // Add click handlers for flag submission
  const submitBtn = document.getElementById('submit-btn');
  if (submitBtn) {
    submitBtn.addEventListener('click', function () {
      const challengeId = this.dataset.challengeId;
      submitFlag(challengeId);
    });
  }

  // Handle Enter key in flag input
  const flagInput = document.getElementById('flag-input');
  if (flagInput) {
    flagInput.addEventListener('keypress', function (e) {
      if (e.key === 'Enter') {
        const challengeId = document.getElementById('submit-btn').dataset.challengeId;
        submitFlag(challengeId);
      }
    });
  }
});

// Cyber Animations
document.addEventListener('DOMContentLoaded', function () {
  // Animated Counter for Stats
  function animateCounter(element, target, duration = 2000) {
    let start = 0;
    const increment = target / (duration / 16);

    function updateCounter() {
      start += increment;
      if (start < target) {
        element.textContent = Math.floor(start);
        requestAnimationFrame(updateCounter);
      } else {
        element.textContent = target;
      }
    }

    updateCounter();
  }

  // Initialize counters when they come into view
  const observerOptions = {
    threshold: 0.5,
    rootMargin: '0px 0px -100px 0px'
  };

  const counterObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const counter = entry.target;
        const target = parseInt(counter.dataset.target);
        animateCounter(counter, target);
        counterObserver.unobserve(counter);
      }
    });
  }, observerOptions);

  // Observe all stat counters
  document.querySelectorAll('.stat-number-cyber').forEach(counter => {
    counterObserver.observe(counter);
  });

  // Animate progress bars
  const progressObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const progressBar = entry.target;
        const width = progressBar.dataset.width;
        setTimeout(() => {
          progressBar.style.width = width + '%';
        }, 500);
        progressObserver.unobserve(progressBar);
      }
    });
  }, observerOptions);

  // Observe all progress bars
  document.querySelectorAll('.progress-bar').forEach(bar => {
    progressObserver.observe(bar);
  });

  // Simple AOS-like animation system
  function initAOS() {
    const elements = document.querySelectorAll('[data-aos]');

    const aosObserver = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          const element = entry.target;
          const delay = element.dataset.aosDelay || 0;

          setTimeout(() => {
            element.classList.add('aos-animate');
          }, delay);

          aosObserver.unobserve(element);
        }
      });
    }, {
      threshold: 0.1,
      rootMargin: '0px 0px -50px 0px'
    });

    elements.forEach(element => {
      aosObserver.observe(element);
    });
  }

  // Initialize AOS animations
  initAOS();

  // Matrix rain effect for background (optional)
  function createMatrixRain() {
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');

    canvas.style.position = 'fixed';
    canvas.style.top = '0';
    canvas.style.left = '0';
    canvas.style.width = '100%';
    canvas.style.height = '100%';
    canvas.style.zIndex = '-1';
    canvas.style.opacity = '0.1';
    canvas.style.pointerEvents = 'none';

    document.body.appendChild(canvas);

    function resizeCanvas() {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    }

    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);

    const chars = '01';
    const fontSize = 14;
    const columns = canvas.width / fontSize;
    const drops = Array(Math.floor(columns)).fill(1);

    function draw() {
      ctx.fillStyle = 'rgba(0, 0, 0, 0.05)';
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      ctx.fillStyle = '#00ff00';
      ctx.font = fontSize + 'px monospace';

      for (let i = 0; i < drops.length; i++) {
        const text = chars[Math.floor(Math.random() * chars.length)];
        ctx.fillText(text, i * fontSize, drops[i] * fontSize);

        if (drops[i] * fontSize > canvas.height && Math.random() > 0.975) {
          drops[i] = 0;
        }
        drops[i]++;
      }
    }

    setInterval(draw, 100);
  }

  // Uncomment to enable matrix rain effect
  // createMatrixRain();
});

// Enhanced Matrix Rain Effect for Hero Section
function createHeroMatrixRain() {
  const heroSection = document.querySelector('.hero-section');
  if (!heroSection) return;

  const canvas = document.createElement('canvas');
  const ctx = canvas.getContext('2d');

  canvas.style.position = 'absolute';
  canvas.style.top = '0';
  canvas.style.left = '0';
  canvas.style.width = '100%';
  canvas.style.height = '100%';
  canvas.style.zIndex = '2';
  canvas.style.opacity = '0.1';
  canvas.style.pointerEvents = 'none';

  heroSection.appendChild(canvas);

  function resizeCanvas() {
    canvas.width = heroSection.offsetWidth;
    canvas.height = heroSection.offsetHeight;
  }

  resizeCanvas();
  window.addEventListener('resize', resizeCanvas);

  const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789@#$%^&*()_+-=[]{}|;:,.<>?';
  const fontSize = 14;
  const columns = canvas.width / fontSize;
  const drops = Array(Math.floor(columns)).fill(1);

  function draw() {
    ctx.fillStyle = 'rgba(0, 0, 0, 0.05)';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    ctx.fillStyle = '#00ff00';
    ctx.font = fontSize + 'px monospace';

    for (let i = 0; i < drops.length; i++) {
      const text = chars[Math.floor(Math.random() * chars.length)];
      ctx.fillText(text, i * fontSize, drops[i] * fontSize);

      if (drops[i] * fontSize > canvas.height && Math.random() > 0.975) {
        drops[i] = 0;
      }
      drops[i]++;
    }
  }

  setInterval(draw, 100);
}

// Initialize enhanced effects
document.addEventListener('DOMContentLoaded', function () {
  // Enable matrix rain effect for hero section
  setTimeout(() => {
    createHeroMatrixRain();
  }, 1000);

  // Add typing effect to terminal command
  const commandElement = document.querySelector('.typing-animation');
  if (commandElement) {
    const text = './start_hacking.sh';
    let i = 0;

    function typeWriter() {
      if (i < text.length) {
        commandElement.textContent = text.substring(0, i + 1);
        i++;
        setTimeout(typeWriter, 150);
      }
    }

    setTimeout(typeWriter, 2000);
  }
});

// Blog Carousel Functionality
function scrollCarousel(direction) {
  const carousel = document.getElementById('blogCarousel');
  if (!carousel) return;

  const scrollAmount = 400;
  const currentScroll = carousel.scrollLeft;

  carousel.scrollTo({
    left: currentScroll + (direction * scrollAmount),
    behavior: 'smooth'
  });
}

// Auto-scroll carousel
function autoScrollCarousel() {
  const carousel = document.getElementById('blogCarousel');
  if (!carousel) return;

  let autoScrollInterval = setInterval(() => {
    const maxScroll = carousel.scrollWidth - carousel.clientWidth;
    if (carousel.scrollLeft >= maxScroll) {
      carousel.scrollTo({ left: 0, behavior: 'smooth' });
    } else {
      carousel.scrollBy({ left: 400, behavior: 'smooth' });
    }
  }, 5000);

  // Pause auto-scroll on hover
  carousel.addEventListener('mouseenter', () => clearInterval(autoScrollInterval));
  carousel.addEventListener('mouseleave', () => {
    autoScrollInterval = setInterval(() => {
      const maxScroll = carousel.scrollWidth - carousel.clientWidth;
      if (carousel.scrollLeft >= maxScroll) {
        carousel.scrollTo({ left: 0, behavior: 'smooth' });
      } else {
        carousel.scrollBy({ left: 400, behavior: 'smooth' });
      }
    }, 5000);
  });
}

// Initialize carousel when DOM is ready
document.addEventListener('DOMContentLoaded', function () {
  autoScrollCarousel();
});


// Image Carousel Functionality
let currentImageIndex = 0;
const images = document.querySelectorAll('.carousel-image');
const totalImages = images.length;
let autoPlayInterval;

function showImage(index) {
  // Remove active class from all images
  images.forEach(img => img.classList.remove('active'));

  // Add active class to current image
  if (images[index]) {
    images[index].classList.add('active');
  }

  // Update dots
  updateDots(index);
}

function nextImage() {
  currentImageIndex = (currentImageIndex + 1) % totalImages;
  showImage(currentImageIndex);
  resetAutoPlay();
}

function prevImage() {
  currentImageIndex = (currentImageIndex - 1 + totalImages) % totalImages;
  showImage(currentImageIndex);
  resetAutoPlay();
}

function updateDots(index) {
  const dots = document.querySelectorAll('.dot');
  dots.forEach((dot, i) => {
    if (i === index) {
      dot.classList.add('active');
    } else {
      dot.classList.remove('active');
    }
  });
}

function createDots() {
  const dotsContainer = document.getElementById('carouselDots');
  if (!dotsContainer) return;

  for (let i = 0; i < totalImages; i++) {
    const dot = document.createElement('div');
    dot.className = 'dot' + (i === 0 ? ' active' : '');
    dot.onclick = () => {
      currentImageIndex = i;
      showImage(currentImageIndex);
      resetAutoPlay();
    };
    dotsContainer.appendChild(dot);
  }
}

function autoPlayCarousel() {
  autoPlayInterval = setInterval(() => {
    nextImage();
  }, 5000);
}

function resetAutoPlay() {
  clearInterval(autoPlayInterval);
  autoPlayCarousel();
}

// Initialize carousel on page load
document.addEventListener('DOMContentLoaded', function () {
  if (images.length > 0) {
    createDots();
    autoPlayCarousel();

    // Pause on hover
    const carousel = document.querySelector('.image-carousel-container');
    if (carousel) {
      carousel.addEventListener('mouseenter', () => clearInterval(autoPlayInterval));
      carousel.addEventListener('mouseleave', () => autoPlayCarousel());
    }
  }
});


// Category Filter Functionality
function initCategoryFilter() {
  const filterBtns = document.querySelectorAll('.filter-btn');
  const challengeCards = document.querySelectorAll('.challenge-card');

  console.log('Filter buttons found:', filterBtns.length);
  console.log('Challenge cards found:', challengeCards.length);

  if (filterBtns.length === 0 || challengeCards.length === 0) {
    console.log('No filter buttons or challenge cards found');
    return;
  }

  filterBtns.forEach(btn => {
    btn.addEventListener('click', function (e) {
      e.preventDefault();
      const selectedCategory = this.getAttribute('data-category');
      console.log('Filter clicked:', selectedCategory);

      // Update active button
      filterBtns.forEach(b => b.classList.remove('active'));
      this.classList.add('active');

      // Filter challenges
      let visibleCount = 0;
      challengeCards.forEach(card => {
        const cardCategory = card.getAttribute('data-category');

        if (selectedCategory === 'all' || cardCategory === selectedCategory) {
          card.style.display = 'block';
          card.style.animation = 'fadeIn 0.3s ease-in';
          visibleCount++;
        } else {
          card.style.display = 'none';
        }
      });
      console.log('Visible cards:', visibleCount);
    });
  });
}

// Initialize filter when DOM is ready
document.addEventListener('DOMContentLoaded', function () {
  initCategoryFilter();
});

// Also try initializing after a short delay to ensure DOM is fully loaded
setTimeout(function () {
  initCategoryFilter();
}, 100);
