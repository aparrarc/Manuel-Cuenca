import { useEffect, useState } from 'react';
import { api } from '../lib/api';
import type { Booking, Catalog, Slot } from '../lib/api';

import { inputClass, madridDate, clock } from '../lib/bookingFormat';
export function SlotButtons({ slots, selected, onSelect, catalog }: { slots: Slot[]; selected?: Slot; onSelect: (s: Slot) => void; catalog: Catalog }) {
    return <div className="mt-4 grid max-h-80 grid-cols-2 gap-2 overflow-y-auto sm:grid-cols-3">
        {slots.map(slot => <button type="button" key={`${slot.start}-${slot.professionalId}`} onClick={() => onSelect(slot)} className={`min-h-16 rounded-xl border px-2 py-2 text-sm ${selected?.start === slot.start && selected.professionalId === slot.professionalId ? 'border-blue-600 bg-blue-600 text-white' : 'border-blue-200 bg-white text-[#071753]'}`}>
            <span className="block font-black">{clock(slot.start)}</span><span className="block text-xs">{catalog.professionals.find(p => p.id === slot.professionalId)?.name}</span>
        </button>)}
    </div>;
}
export function BookingManager({ booking, catalog, token = '', onChanged }: { booking: Booking; catalog: Catalog; token?: string; onChanged: (b: Booking) => void }) {
    const [editing, setEditing] = useState(false);
    const [date, setDate] = useState(booking.start.slice(0, 10));
    const [professional, setProfessional] = useState(booking.professionalId);
    const [slots, setSlots] = useState<Slot[]>([]);
    const [selected, setSelected] = useState<Slot>();
    const [loading, setLoading] = useState(false);
    const [busy, setBusy] = useState(false);
    const [error, setError] = useState('');
    const [revision, setRevision] = useState(0);
    const service = catalog.services.find(s => s.id === booking.serviceId);
    useEffect(() => {
        if (!editing) return;
        const controller = new AbortController(); setSelected(undefined); setSlots([]); setLoading(true); setError('');
        api.availability(booking.serviceId, date, professional, controller.signal).then(r => { if (!controller.signal.aborted) setSlots(r.slots); }).catch(e => { if (!controller.signal.aborted) setError(e.message); }).finally(() => { if (!controller.signal.aborted) setLoading(false); });
        return () => controller.abort();
    }, [editing, date, professional, booking.serviceId, revision]);
    const cancel = async () => {
        if (busy || !window.confirm('¿Cancelar esta cita de demostración? El hueco quedará libre.')) return;
        setBusy(true); setError('');
        try { const r = await api.cancelBooking(booking.id, token || undefined); onChanged(r.booking); setEditing(false); }
        catch (e) { setError(e instanceof Error ? e.message : 'No se pudo cancelar.'); }
        finally { setBusy(false); }
    };
    const move = async () => {
        if (!selected || busy) return;
        setBusy(true); setError('');
        try {
            const r = await api.updateBooking(booking.id, token, { start: selected.start, professionalId: selected.professionalId, idempotencyKey: crypto.randomUUID() });
            onChanged(r.booking); setEditing(false);
        } catch (e) { setRevision(x => x + 1); setError(e instanceof Error ? e.message : 'No se pudo cambiar.'); }
        finally { setBusy(false); }
    };
    return <div className="mt-4">
        {booking.status === 'cancelled' ? <p className="font-bold text-red-700">Cita cancelada · hueco liberado</p> : <div className="flex flex-wrap gap-3">
            <button type="button" disabled={busy} onClick={() => setEditing(!editing)} className="min-h-11 rounded-full border border-blue-300 px-4 text-sm font-bold text-blue-700">Cambiar cita</button>
            <button type="button" disabled={busy} onClick={cancel} className="min-h-11 rounded-full border border-red-200 px-4 text-sm font-bold text-red-700">Cancelar cita</button>
        </div>}
        {editing && booking.status !== 'cancelled' && <fieldset disabled={busy} className="mt-4 rounded-2xl bg-blue-50 p-4">
            <legend className="font-bold">Elige el nuevo hueco</legend>
            <label className="block text-sm font-bold">Nueva fecha<input type="date" min={madridDate()} value={date} onChange={e => setDate(e.target.value)} className={inputClass} /></label>
            <label className="mt-3 block text-sm font-bold">Nuevo profesional<select aria-label="Nuevo profesional" value={professional} onChange={e => setProfessional(e.target.value)} className={inputClass}>{catalog.professionals.filter(p => service?.professionalIds.includes(p.id)).map(p => <option key={p.id} value={p.id}>{p.name}</option>)}</select></label>
            {loading ? <p className="mt-4">Consultando huecos…</p> : slots.length ? <SlotButtons slots={slots} selected={selected} onSelect={setSelected} catalog={catalog} /> : <p className="mt-4">No hay huecos. Prueba otra fecha.</p>}
            <button type="button" disabled={!selected || busy} onClick={move} className="mt-4 min-h-12 rounded-full bg-blue-600 px-5 font-bold text-white disabled:opacity-40">Guardar cambio</button>
        </fieldset>}
        {error && <p role="alert" className="mt-3 text-sm text-red-700">{error}</p>}
    </div>;
}
