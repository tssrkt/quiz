'use strict';
const assert = require('node:assert/strict');
const core = require('../js/quiz.js');

function makeQuiz(published = true) {
  return {
    slug: 'demo-quiz', title: 'Демо', intro: 'Вступление', published, content_version: 'a'.repeat(64),
    questions: [
      { id: 'question-01', question: 'Первый?', explanation: 'Пояснение 1', answers: [{ id: 'a-01', text: 'Да', correct: true }, { id: 'a-02', text: 'Нет', correct: false }] },
      { id: 'question-02', question: 'Второй?', explanation: 'Пояснение 2', answers: [{ id: 'a-01', text: 'Нет', correct: false }, { id: 'a-02', text: 'Да', correct: true }] }
    ]
  };
}
function answerAndAdvance(state, quiz, answerId) {
  const answered = core.answerQuestion(state, quiz, answerId, '2026-01-01T00:00:00.000Z');
  const advanced = core.advance(answered.state, quiz, '2026-01-01T00:00:01.000Z');
  return { answered, advanced };
}

const quiz = makeQuiz(true);
assert.equal(core.validateQuiz(quiz), true, '1: опубликованная викторина валидна');
assert.equal(core.canOpenQuiz(quiz, false), true, '1: опубликованная открывается');
assert.equal(core.canOpenQuiz(makeQuiz(false), true), true, '2: черновик открывается в preview');
assert.equal(core.canOpenQuiz(makeQuiz(false), false), false, '3: черновик закрыт без preview');
assert.equal(core.validateQuiz({}), false, 'повреждённые данные отклоняются');

let state = core.freshState(quiz, '2026-01-01T00:00:00.000Z');
const correct = core.answerQuestion(state, quiz, 'a-01');
assert.equal(correct.accepted, true); assert.equal(correct.correct, true); assert.equal(correct.state.correct_count, 1, '4: первый правильный ответ');
const repeated = core.answerQuestion(correct.state, quiz, 'a-02');
assert.equal(repeated.accepted, false); assert.equal(repeated.state.correct_count, 1, '6: повторный выбор заблокирован');
assert.equal(core.autoAdvanceDelay(true), 800, '7: правильный ответ переходит через 800 мс');
assert.equal(core.autoAdvanceDelay(false), null, '8: неправильный ответ не переходит автоматически');
assert.equal(quiz.questions[0].explanation, 'Пояснение 1', '9: пояснение доступно для неправильного ответа');

state = core.freshState(quiz);
const wrong = core.answerQuestion(state, quiz, 'a-02');
assert.equal(wrong.accepted, true); assert.equal(wrong.correct, false); assert.equal(wrong.state.correct_count, 0, '5: первый неправильный ответ');
const moved = core.advance(wrong.state, quiz);
assert.equal(moved.advanced, true); assert.equal(moved.state.current_index, 1, '9: кнопка переводит дальше');
const notDouble = core.advance(moved.state, quiz);
assert.equal(notDouble.advanced, false); assert.equal(notDouble.state.current_index, 1, '20: двойной переход невозможен');
const last = answerAndAdvance(moved.state, quiz, 'a-02');
assert.equal(last.advanced.state.completed, true); assert.equal(last.advanced.state.current_index, 2, '10: последний вопрос завершает попытку');
assert.equal(last.advanced.state.correct_count, 1, '11: правильные ответы подсчитаны');
assert.equal(core.resultPercent(34, 40), 85, '12: процент округляется');
assert.match(core.resultRecommendation(49), /^Что ж, некоторые вопросы/);
assert.match(core.resultRecommendation(50), /^Неплохой результат!/);
assert.match(core.resultRecommendation(74), /^Неплохой результат!/);
assert.match(core.resultRecommendation(75), /^Хороший результат!/);
assert.match(core.resultRecommendation(99), /^Хороший результат!/);
assert.equal(core.resultRecommendation(100), null, 'при 100% рекомендательный блок отсутствует');
assert.equal(core.resultMessage(90), 'Отличный результат!');
assert.equal(core.resultMessage(89), 'Очень хороший результат!');
assert.equal(core.resultMessage(74), 'Неплохо, но есть что повторить.');
assert.equal(core.resultMessage(49), 'Попробуйте пройти викторину ещё раз.', '13: все диапазоны оценок');

const saved = JSON.stringify(moved.state);
const restored = core.restoreState(saved, quiz);
assert.equal(restored.current_index, 1); assert.equal(restored.answers['question-01'].answer_id, 'a-02', '14: сохранение восстановлено');
const restarted = core.freshState(quiz);
assert.equal(restarted.current_index, 0); assert.equal(Object.keys(restarted.answers).length, 0, '15: начало заново');
const changedQuiz = makeQuiz(); changedQuiz.questions[0].answers.push({ id: 'a-03', text: 'Может быть', correct: false });
const incompatible = core.restoreState(saved, changedQuiz);
assert.equal(incompatible.current_index, 0); assert.equal(Object.keys(incompatible.answers).length, 0, '16: несовместимое сохранение сброшено');
for (const mutate of [
  (value) => { value.questions[0].question = 'Изменённый вопрос?'; },
  (value) => { value.questions[0].explanation = 'Новое объяснение'; },
  (value) => { value.questions[0].answers[0].text = 'Изменённый ответ'; },
  (value) => { value.questions.reverse(); },
  (value) => { value.questions.push({ id: 'question-03', question: 'Третий?', image: 'img/quiz/demo/03.webp', explanation: 'Пояснение 3', answers: [{ id: 'a-01', text: 'Да', correct: true }, { id: 'a-02', text: 'Нет', correct: false }] }); }
]) {
  const changed = makeQuiz(); mutate(changed);
  assert.equal(core.restoreState(saved, changed).current_index, 0, 'изменение содержимого сбрасывает прогресс');
}
assert.equal(core.versionedUrl('data/quizzes/horse-colors.json', 'abc123'), 'data/quizzes/horse-colors.json?v=abc123');
assert.equal(core.versionedUrl('img/quiz/horse-colors/01.webp', 'abc123'), 'img/quiz/horse-colors/01.webp?v=abc123');

assert.equal(core.shareText({ title: 'Масти лошадей' }, 34, 40), 'Мой результат — 34 из 40 (85%) в викторине «Масти лошадей». А какой результат будет у вас?', '17: текст публикации');
assert.equal(core.directQuizUrl('https://example.test/quiz/quiz.html?quiz=x&preview=1', 'horse-colors'), 'https://example.test/quiz/quiz.html?quiz=horse-colors');
assert.equal(core.shareMethod(false), 'copy', '18: fallback без Web Share');
assert.equal(core.shareMethod(true), 'share');
assert.equal(core.prefersReducedMotion(() => ({ matches: true })), true);
assert.equal(core.shouldConfetti(true, true), false); assert.equal(core.shouldConfetti(true, false), true, '19: reduced motion отключает конфетти');

function runScenario(answerIds, closeAfterFirst = false) {
  let attempt = core.freshState(quiz);
  answerIds.forEach((answerId, index) => {
    const step = answerAndAdvance(attempt, quiz, answerId); attempt = step.advanced.state;
    if (closeAfterFirst && index === 0) attempt = core.restoreState(JSON.stringify(attempt), quiz);
  });
  return attempt;
}
assert.equal(runScenario(['a-01', 'a-02']).correct_count, 2, 'сценарий: все правильные');
assert.equal(runScenario(['a-02', 'a-01']).correct_count, 0, 'сценарий: все неправильные');
const mixed = runScenario(['a-01', 'a-01'], true);
assert.equal(mixed.correct_count, 1); assert.equal(mixed.completed, true, 'сценарий: смешанный с восстановлением');

console.log('quiz.test.js: 20 требований и 3 сценария пройдены');
