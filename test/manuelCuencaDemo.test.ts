import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';

const brandSource = readFileSync(new URL('../src/config/brands/manuelcuenca.ts', import.meta.url), 'utf8');
const bookingSource = readFileSync(new URL('../src/pages/ManuelCuencaBooking.tsx', import.meta.url), 'utf8');
const landingSource = readFileSync(new URL('../src/pages/ManuelCuencaLanding.tsx', import.meta.url), 'utf8');
const appSource = readFileSync(new URL('../src/App.tsx', import.meta.url), 'utf8');

test('la candidata usa una landing y una reserva exclusivas para Manuel Cuenca', () => {
    assert.match(appSource, /element={<ManuelCuencaLanding \/>}/);
    assert.match(appSource, /element={<ManuelCuencaBooking \/>}/);
    assert.match(landingSource, /Manuel Cuenca Fisioterapia/);
    assert.doesNotMatch(landingSource, /barber|peluquer|corte|ritual/i);
    assert.doesNotMatch(bookingSource, /barber|peluquer|corte|ritual/i);
});

test('la agenda demo presenta cinco áreas y marca entrenamiento como pendiente', () => {
    const departmentIds = bookingSource.match(/id: '(fisioterapia|osteopatia|nutricion|psicologia|entrenamiento)'/g) ?? [];
    assert.equal(departmentIds.length, 5);
    assert.match(bookingSource, /id: 'entrenamiento',[\s\S]*?enabled: false/);
    assert.match(bookingSource, /No se creará ninguna cita ni se enviará ninguna notificación/);
});

test('el equipo publicado refleja cinco fisioterapeutas y un entrenador', () => {
    for (const name of ['Manuel Cuenca', 'Fernándo López', 'Álvaro Hurtado', 'Víctor González', 'Alex Velasco', 'José David López']) {
        assert.match(brandSource, new RegExp(name));
    }
    assert.equal((brandSource.match(/Fisioterapeuta/g) ?? []).length, 5);
    assert.equal((brandSource.match(/Entrenador personal/g) ?? []).length, 1);
});
