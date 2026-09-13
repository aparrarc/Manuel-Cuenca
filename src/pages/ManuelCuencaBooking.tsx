import { useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { api, savedReservations, saveReservation } from '../lib/api';
import type { Booking, Catalog, Slot } from '../lib/api';
import { BookingManager, SlotButtons } from '../components/BookingManager';
import { inputClass, madridDate, appointmentDate } from '../lib/bookingFormat';

export default function ManuelCuencaBooking() {
    const [catalog, setCatalog] = useState<Catalog>();
    const [department, setDepartment] = useState(''); const [serviceId, setServiceId] = useState(''); const [professional, setProfessional] = useState('');
    const [date, setDate] = useState(madridDate()); const [slots, setSlots] = useState<Slot[]>([]); const [selected, setSelected] = useState<Slot>();
    const [name, setName] = useState(''); const [phone, setPhone] = useState(''); const [error, setError] = useState('');
    const [loading, setLoading] = useState(false); const [busy, setBusy] = useState(false); const [revision, setRevision] = useState(0);
    const [reservations, setReservations] = useState<{ booking: Booking; token: string }[]>([]);
    const [confirmed, setConfirmed] = useState<string>();
    const retry = useRef<{ fingerprint: string; key: string } | undefined>(undefined);
    useEffect(() => {
        let active = true;
        api.catalog().then(c => { if (active) { setCatalog(c); setDepartment(c.departments.find(d => d.enabled)?.id || ''); } }).catch(e => { if (active) setError(e.message); });
        Promise.all(savedReservations().map(async saved => { try { return { booking: (await api.getBooking(saved.id, saved.token)).booking, token: saved.token }; } catch { return null; } })).then(items => { if (active) setReservations(items.filter((i): i is { booking: Booking; token: string } => i !== null)); });
        return () => { active = false; };
    }, []);
    useEffect(() => {
        const controller = new AbortController(); setSelected(undefined); setSlots([]);
        if (!serviceId || !date) { setLoading(false); return; }
        setLoading(true);
        api.availability(serviceId, date, professional || undefined, controller.signal).then(r => { if (!controller.signal.aborted) setSlots(r.slots); }).catch(e => { if (!controller.signal.aborted) setError(e.message); }).finally(() => { if (!controller.signal.aborted) setLoading(false); });
        return () => controller.abort();
    }, [serviceId, professional, date, revision]);
    const changed = (b: Booking) => setReservations(items => items.map(i => i.booking.id === b.id ? { ...i, booking: b } : i));
    const submit = async (event: React.FormEvent) => {
        event.preventDefault(); if (!selected || busy) return;
        setBusy(true); setError('');
        const payload = { serviceId, professionalId: selected.professionalId, start: selected.start, customerName: name.trim(), phone: phone.trim() };
        const fingerprint = JSON.stringify(payload);
        if (retry.current?.fingerprint !== fingerprint) retry.current = { fingerprint, key: crypto.randomUUID() };
        try {
            const result = await api.createBooking({ ...payload, idempotencyKey: retry.current.key });
            saveReservation({ id: result.booking.id, token: result.managementToken });
            setReservations(items => [{ booking: result.booking, token: result.managementToken }, ...items.filter(i => i.booking.id !== result.booking.id)]);
            setConfirmed(result.booking.id); setSelected(undefined); setRevision(x => x + 1);
        } catch (e) { setError(e instanceof Error ? e.message : 'No se pudo reservar.'); setRevision(x => x + 1); }
        finally { setBusy(false); }
    };
    const service = catalog?.services.find(s => s.id === serviceId);
    const confirmation = reservations.find(r => r.booking.id === confirmed);
    return <div className="min-h-screen bg-[#f7f9fc] text-[#071753]">
        <header className="border-b bg-white"><div className="mx-auto flex min-h-20 max-w-6xl items-center justify-between px-5"><Link to="/" className="font-bold">← Volver a la web</Link><span className="text-sm font-bold">Manuel Cuenca · Demo</span></div></header>
        <main className="mx-auto max-w-6xl px-5 py-10">
            <h1 className="text-3xl font-black sm:text-5xl">Reserva tu cita</h1>
            <p className="mt-4 rounded-xl border border-blue-200 bg-blue-50 p-4 text-sm">Agenda de demostración: utiliza nombre y teléfono ficticios. Las reservas se guardan, pero no son citas clínicas reales ni se envían avisos. Horarios y tratamientos pendientes de validación con el centro.</p>
            {confirmation && catalog ? <section className="mt-6 rounded-2xl bg-white p-6 shadow-sm">
                <h2 className="text-2xl font-black">Cita de demostración guardada</h2><p className="mt-3">{appointmentDate(confirmation.booking.start)} · {catalog.professionals.find(p => p.id === confirmation.booking.professionalId)?.name}</p><p>{confirmation.booking.customerName}</p>
                <BookingManager booking={confirmation.booking} token={confirmation.token} catalog={catalog} onChanged={changed} />
                <button onClick={() => { setConfirmed(undefined); setRevision(x => x + 1); }} className="mt-5 min-h-12 rounded-full bg-blue-600 px-6 font-bold text-white">Reservar otra cita</button>
            </section> : <form onSubmit={submit} className="mt-8">
                <fieldset disabled={busy || !catalog} className="space-y-6">
                    <section className="rounded-2xl bg-white p-6 shadow-sm"><h2 className="text-xl font-black">1. Servicio y profesional</h2><div className="mt-4 grid gap-4 md:grid-cols-3">
                        <label className="font-bold">Área<select aria-label="Área" className={inputClass} value={department} onChange={e => { setDepartment(e.target.value); setServiceId(''); setProfessional(''); setSelected(undefined); setSlots([]); setError(''); }}><option value="">Selecciona</option>{catalog?.departments.map(d => <option key={d.id} value={d.id} disabled={!d.enabled}>{d.name}{!d.enabled ? ' · sin profesional asignado' : ''}</option>)}</select></label>
                        <label className="font-bold">Servicio<select aria-label="Servicio" required className={inputClass} value={serviceId} onChange={e => { setServiceId(e.target.value); setProfessional(''); setSelected(undefined); setSlots([]); setError(''); }}><option value="">Selecciona</option>{catalog?.services.filter(s => s.department === department).map(s => <option key={s.id} value={s.id}>{s.name} · {s.duration} min</option>)}</select></label>
                        <label className="font-bold">Profesional<select aria-label="Profesional" className={inputClass} value={professional} onChange={e => { setProfessional(e.target.value); setSelected(undefined); setError(''); }}><option value="">Cualquiera disponible</option>{catalog?.professionals.filter(p => service?.professionalIds.includes(p.id)).map(p => <option key={p.id} value={p.id}>{p.name}</option>)}</select></label>
                    </div></section>
                    <section className="rounded-2xl bg-white p-6 shadow-sm"><h2 className="text-xl font-black">2. Fecha y hora · Málaga</h2><label className="mt-4 block max-w-sm font-bold">Fecha<input required type="date" min={madridDate()} className={inputClass} value={date} onChange={e => { setDate(e.target.value); setSelected(undefined); setError(''); }} /></label>
                        {loading ? <p className="mt-5">Consultando disponibilidad…</p> : slots.length && catalog ? <SlotButtons slots={slots} selected={selected} onSelect={setSelected} catalog={catalog} /> : <p className="mt-5 text-slate-500">{serviceId ? 'No hay huecos. Prueba otra fecha o profesional.' : 'Selecciona primero el servicio.'}</p>}
                    </section>
                    <section className="rounded-2xl bg-white p-6 shadow-sm"><h2 className="text-xl font-black">3. Datos ficticios para la demo</h2><div className="mt-4 grid gap-4 sm:grid-cols-2"><label className="font-bold">Nombre<input required minLength={2} maxLength={120} className={inputClass} value={name} onChange={e => setName(e.target.value)} placeholder="Persona Demo" /></label><label className="font-bold">Teléfono<input required minLength={3} maxLength={40} type="tel" className={inputClass} value={phone} onChange={e => setPhone(e.target.value)} placeholder="600000000" /></label></div></section>
                    <button type="submit" disabled={!selected || busy} className="min-h-14 rounded-full bg-[#2f85e8] px-8 font-black text-white disabled:opacity-40">{busy ? 'Guardando…' : 'Confirmar cita'}</button>
                </fieldset>
                {error && <p role="alert" className="mt-4 rounded-xl bg-red-50 p-4 text-red-700">{error}</p>}
            </form>}
            {!confirmed && catalog && reservations.length > 0 && <section className="mt-10"><h2 className="text-2xl font-black">Mis reservas en este navegador</h2><p className="mt-2 text-sm text-slate-500">Disponibles mientras conserves esta sesión del navegador.</p>{reservations.map(r => <article key={r.booking.id} className="mt-4 rounded-2xl bg-white p-5"><p className="font-bold">{appointmentDate(r.booking.start)} · {catalog.professionals.find(p => p.id === r.booking.professionalId)?.name}</p><p>{r.booking.customerName}</p><BookingManager booking={r.booking} token={r.token} catalog={catalog} onChanged={changed} /></article>)}</section>}
            <Link to="/admin" className="mt-8 inline-block min-h-11 py-3 font-bold text-blue-700">Acceso de recepción</Link>
        </main>
    </div>;
}
