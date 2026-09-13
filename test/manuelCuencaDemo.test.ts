import assert from 'node:assert/strict';
import test from 'node:test';
import { clock } from '../src/lib/bookingFormat.ts';

test('las horas se muestran en Madrid, incluso si el timestamp viene en UTC', () => {
    assert.equal(clock('2026-09-14T07:00:00Z'), '09:00');
    assert.equal(clock('2026-12-14T08:00:00Z'), '09:00');
});
test('el cambio de hora de otoño usa el offset correspondiente a cada instante', () => {
    assert.equal(clock('2026-10-25T00:30:00Z'), '02:30');
    assert.equal(clock('2026-10-25T01:30:00Z'), '02:30');
});
