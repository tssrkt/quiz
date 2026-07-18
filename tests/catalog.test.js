'use strict';

const assert = require('node:assert/strict');
const {
  PAGE_SIZE,
  sortQuizzes,
  arrangeQuizzes,
  countTags,
  paginationItems,
  getStateFromUrl,
  buildUrl
} = require('../js/quizzes.js');

function quiz(index, overrides = {}) {
  return {
    slug: `quiz-${index}`,
    title: `Викторина ${String(index).padStart(3, '0')}`,
    publication_date: `2026-01-${String((index % 28) + 1).padStart(2, '0')}`,
    tags: index % 2 ? ['horses'] : ['biology', 'horses'],
    ...overrides
  };
}

function pagesFor(count) {
  return Math.max(1, Math.ceil(Array.from({ length: count }, (_, index) => quiz(index)).length / PAGE_SIZE));
}

assert.equal(PAGE_SIZE, 25);
assert.equal(pagesFor(0), 1);
assert.equal(pagesFor(1), 1);
assert.equal(pagesFor(25), 1);
assert.equal(pagesFor(26), 2);
assert.equal(pagesFor(61), 3);
assert.equal(Array.from({ length: 26 }).slice(PAGE_SIZE).length, 1);
assert.equal(Array.from({ length: 61 }).slice(PAGE_SIZE * 2).length, 11);

const grouped = arrangeQuizzes([
  quiz(1, { slug: 'other-new', title: 'Яблоко', publication_date: '2026-04-01', tags: ['biology'] }),
  quiz(2, { slug: 'match-old', title: 'Бета', publication_date: '2025-01-01', tags: ['horses'] }),
  quiz(3, { slug: 'match-new', title: 'Альфа', publication_date: '2026-03-01', tags: ['horses', 'biology'] }),
  quiz(4, { slug: 'other-old', title: 'Гамма', publication_date: '2024-01-01', tags: ['biology'] })
], 'horses', 'new');
assert.deepEqual(grouped.map((item) => item.slug), ['match-new', 'match-old', 'other-new', 'other-old']);
assert.equal(new Set(grouped.map((item) => item.slug)).size, grouped.length);
const counts = countTags(grouped, [{ slug: 'horses' }, { slug: 'biology' }]);
assert.equal(counts.get('horses'), 2);
assert.equal(counts.get('biology'), 3);
assert.equal(counts.has('hidden'), false);

const dated = [
  quiz(1, { title: 'Бета', publication_date: '2026-02-01' }),
  quiz(2, { title: 'Альфа', publication_date: '2026-02-01' }),
  quiz(3, { title: 'Ошибка даты', publication_date: '2026-99-99' }),
  quiz(4, { title: 'Старая', publication_date: '2025-01-01' })
];
assert.deepEqual(sortQuizzes(dated, 'new').map((item) => item.title), ['Альфа', 'Бета', 'Старая', 'Ошибка даты']);
assert.deepEqual(sortQuizzes(dated, 'old').map((item) => item.title), ['Старая', 'Альфа', 'Бета', 'Ошибка даты']);
assert.deepEqual(sortQuizzes(dated, 'az').map((item) => item.title), ['Альфа', 'Бета', 'Ошибка даты', 'Старая']);

assert.deepEqual(paginationItems(1, 1), []);
assert.deepEqual(paginationItems(1, 12), [1, 2, 'ellipsis', 12]);
assert.deepEqual(paginationItems(6, 12), [1, 'ellipsis', 5, 6, 7, 'ellipsis', 12]);
assert.deepEqual(paginationItems(12, 12), [1, 'ellipsis', 11, 12]);

const visible = new Set(['horses', 'biology']);
assert.deepEqual(getStateFromUrl('?tag=horses&sort=old&page=2', visible, 3), { tag: 'horses', sort: 'old', page: 2 });
assert.deepEqual(getStateFromUrl('?tag=hidden&sort=popular&page=999', visible, 3), { tag: 'all', sort: 'new', page: 3 });
assert.deepEqual(getStateFromUrl('?page=-4', visible, 3), { tag: 'all', sort: 'new', page: 1 });
const url = buildUrl('https://example.test/quiz/quizzes.html?source=email&tag=horses', { tag: 'all', sort: 'az', page: 1 });
assert.equal(url, '/quiz/quizzes.html?source=email&sort=az&page=1');

console.log('catalog.test.js: все проверки пройдены');
