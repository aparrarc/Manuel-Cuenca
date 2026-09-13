import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../lib/api';
import type { Booking, Catalog } from '../lib/api';
import { BookingManager } from '../components/BookingManager';
import { clock, madridDate } from '../lib/bookingFormat';

export default function ManuelCuencaAdmin() {
    const [authenticated, setAuthenticated] = useState<boolean>(); const [password, setPassword] = useState('');
    const [catalog, setCatalog] = useState<Catalog>(); const [date, setDate] = useState(madridDate()); const [bookings, setBookings] = useState<Booking[]>([]);
    const [error, setError] = useState(''); const [busy, setBusy] = useState(false); const [revision, setRevision] = useState(0);
    useEffect(() => { api.adminSession().then(d => setAuthenticated(d.authenticated)).catch(() => setAuthenticated(false)); api.catalog().then(setCatalog).catch(e => setError(e.message)); }, []);
    useEffect(() => {
        if (!authenticated || !date) return;
        let active = true; let pending = false; setBookings([]);
        const refresh = async () => {
            if (pending) return; pending = true;
            try { const result = await api.adminBookings(date); if (active) { setBookings(result.bookings); setError(''); } }
            catch (e) { if (active) setError(e instanceof Error ? e.message : 'No se pudo actualizar la agenda.'); }
            finally { pending = false; }
        };
        refresh(); const interval = window.setInterval(refresh, 15000);
        return () => { active = false; window.clearInterval(interval); };
    }, [authenticated, date, revision]);
    const login = async (event: React.FormEvent) => {
        event.preventDefault(); if (busy) return; setBusy(true); setError('');
        try { await api.adminLogin(password); setAuthenticated(true); setPassword(''); }
        catch (e) { setError(e instanceof Error ? e.message : 'No se pudo iniciar sesión.'); }
        finally { setBusy(false); }
    };
    if (authenticated === undefined) return <main className="p-8">Comprobando acceso…</main>;
    if (!authenticated) return <main className="grid min-h-screen place-items-center bg-[#f7f9fc] p-5 text-[#071753]"><form onSubmit={login} className="w-full max-w-md rounded-3xl bg-white p-8 shadow-xl"><Link to="/booking" className="font-bold text-blue-700">← Volver a reservas</Link><h1 className="mt-7 text-3xl font-black">Agenda de recepción</h1><p className="mt-3 text-sm">Seis calendarios · Manuel Cuenca</p><label className="mt-6 block font-bold">Contraseña<input autoComplete="current-password" required type="password" value={password} onChange={e => setPassword(e.target.value)} className="mt-2 min-h-12 w-full rounded-xl border border-blue-200 px-3" /></label>{error && <p role="alert" className="mt-3 text-sm text-red-700">{error}</p>}<button disabled={busy} className="mt-6 min-h-12 w-full rounded-full bg-blue-600 font-bold text-white">{busy ? 'Entrando…' : 'Entrar'}</button></form></main>;
    return <div className="min-h-screen bg-[#f7f9fc] text-[#071753]">
        <header className="border-b bg-white px-5 py-5"><div className="mx-auto flex max-w-[1800px] flex-wrap items-center justify-between gap-4"><div><p className="text-sm font-bold text-blue-600">Manuel Cuenca · Demo</p><h1 className="text-3xl font-black">Agenda de recepción</h1></div><div className="flex flex-wrap items-center gap-3"><label className="text-sm font-bold">Fecha de agenda<input type="date" aria-label="Fecha de agenda" value={date} onChange={e => setDate(e.target.value)} className="ml-2 min-h-11 rounded-xl border px-3" /></label><button onClick={() => setRevision(x => x + 1)} className="min-h-11 rounded-full border px-4 font-bold">Actualizar</button><button onClick={async () => { try { await api.adminLogout(); setAuthenticated(false); } catch { setError('No se pudo cerrar sesión.'); } }} className="min-h-11 rounded-full border px-4 font-bold">Salir</button></div></div></header>
        <main className="mx-auto max-w-[1800px] px-5 py-7"><div className="mb-5 flex flex-wrap items-center justify-between gap-3"><p className="max-w-3xl text-sm text-slate-600">Una agenda por profesional. Actualización cada 15 segundos. Horarios de demostración: lunes a viernes, 08–14 y 16–20. Solo datos ficticios.</p><Link to="/booking" className="min-h-11 rounded-full bg-blue-600 px-5 py-3 font-bold text-white">Crear cita</Link></div>
            {error && <p role="alert" className="mb-4 rounded-xl bg-red-50 p-4 text-red-700">{error}</p>}
            <div className="flex gap-4 overflow-x-auto pb-5">{catalog?.professionals.map(pro => <section key={pro.id} className="min-w-[260px] flex-1 rounded-2xl bg-white p-4 shadow-sm"><h2 className="border-b pb-3 font-black">{pro.name}</h2><p className="mt-2 text-xs text-slate-500">{pro.role === 'trainer' ? 'Entrenamiento personal' : 'Fisioterapia'}</p>
                {bookings.filter(b => b.professionalId === pro.id).map(b => <article key={b.id} className={`mt-4 rounded-xl border border-blue-100 p-3 ${b.status === 'cancelled' ? 'bg-slate-50' : 'bg-blue-50/50'}`}><p className="font-black">{clock(b.start)}–{clock(b.end)}</p><p className="font-bold">{b.customerName}</p><p className="text-xs text-slate-600">{catalog.services.find(s => s.id === b.serviceId)?.name} · {b.phone}</p><BookingManager booking={b} catalog={catalog} onChanged={() => setRevision(x => x + 1)} /></article>)}
                {!bookings.some(b => b.professionalId === pro.id) && <p className="py-10 text-center text-sm text-slate-400">Sin citas</p>}
            </section>)}</div>
        </main>
    </div>;
}
