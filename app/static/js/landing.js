document.documentElement.classList.add('js');

const form = document.querySelector('#demo-search');
const input = document.querySelector('#search-input');
const queryLabel = document.querySelector('#demo-query');
const status = document.querySelector('#result-status');
const promptButtons = document.querySelectorAll('[data-query]');
const cards = document.querySelectorAll('.place-card[data-place]');
const categoryItems = document.querySelectorAll('[data-category]');
const newSearchButton = document.querySelector('.new-search');
let currentExampleIndex = 0;

const places = {
  'night-owl': {
    name: 'Night Owl Café',
    rating: '4.8 ★★★★★',
    reviews: '(342)',
    image: '/static/images/night-owl-detail.webp',
    matches: [
      'Quiet atmosphere',
      'Plenty of outlets',
      'Reliable Wi-Fi',
      'Late hours',
      'Student friendly',
    ],
  },
  brewed: {
    name: 'Brewed Awakenings',
    rating: '4.6 ★★★★★',
    reviews: '(198)',
    image: '/static/images/brewed-awakenings.webp',
    matches: [
      'Calm seating',
      'Open late',
      'Strong Wi-Fi',
      'Good coffee',
      'Easy walk',
    ],
  },
  common: {
    name: 'Common Grounds',
    rating: '4.5 ★★★★★',
    reviews: '(276)',
    image: '/static/images/common-grounds.webp',
    matches: [
      'Cozy atmosphere',
      'Reliable Wi-Fi',
      'Affordable',
      'Open seating',
      'Student friendly',
    ],
  },
};

function runDemo(query) {
  const clean = query.trim() || 'A quiet café with outlets, open late.';
  queryLabel.textContent = clean;
  status.textContent = 'Loading sample results…';
  document.querySelector('.product-stage').classList.add('is-searching');
  window.setTimeout(() => {
    status.textContent = '3 sample results';
    document.querySelector('.product-stage').classList.remove('is-searching');
  }, 650);
  document.querySelector('#discover').scrollIntoView({behavior:'smooth', block:'center'});
}

form.addEventListener('submit', event => {
  event.preventDefault();

  const query = input.value.trim();

  if (!query) {
    input.focus();
    return;
  }

  window.location.href = form.action;
});
promptButtons.forEach(button => button.addEventListener('click', () => { input.value = button.dataset.query; runDemo(button.dataset.query); }));
newSearchButton.addEventListener('click', () => {
  currentExampleIndex = (currentExampleIndex + 1) % promptButtons.length;
  const query = promptButtons[currentExampleIndex].dataset.query;
  input.value = query;
  runDemo(query);
});
categoryItems.forEach(item => item.addEventListener('click', event => {
  event.preventDefault();
  const query = item.dataset.category;
  input.value = query;
  runDemo(query);
}));

cards.forEach(card => card.addEventListener('click', event => {
  if (event.target.closest('button')) return;
  cards.forEach(item => item.classList.remove('selected'));
  card.classList.add('selected');
  const place = places[card.dataset.place];
  document.querySelector('#detail-name').textContent = place.name;
  document.querySelector('#detail-rating').textContent = place.rating;
  document.querySelector('#detail-reviews').textContent = place.reviews;
  const image = document.querySelector('#detail-image');
  image.src = place.image;
  image.alt = `${place.name} interior`;
  document.querySelector('#match-list').innerHTML = place.matches.map(item => `<li>${item}</li>`).join('');
}));

const revealElements = document.querySelectorAll('.reveal');

if ('IntersectionObserver' in window) {
  const revealObserver = new IntersectionObserver(
    (entries, observer) => {
      entries.forEach(entry => {
        if (!entry.isIntersecting) return;
        entry.target.classList.add('is-visible');
        observer.unobserve(entry.target);
      });
    },
    {
      threshold: 0.24,
      rootMargin: '0px 0px -80px 0px'
    }
  );

  revealElements.forEach(element => revealObserver.observe(element));
} else {
  revealElements.forEach(element => element.classList.add('is-visible'));
}
