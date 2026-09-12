import { useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import {
    Activity,
    ArrowLeft,
    ArrowRight,
    Brain,
    CalendarDays,
    Check,
    Clock3,
    Dumbbell,
    HeartPulse,
    Info,
    Salad,
    ShieldCheck,
    UserRound,
} from 'lucide-react';

type Department = {
    id: string;
    name: string;
    description: string;
    enabled: boolean;
    icon: typeof Activity;
    services: string[];
    professionals: string[];
};

const departments: Department[] = [
    {
        id: 'fisioterapia',
        name: 'Fisioterapia y rehabilitación',
        description: 'Valoración, fisioterapia avanzada, deportiva, suelo pélvico y recuperación funcional.',
        enabled: true,
        icon: Activity,
        services: ['Primera valoración de fisioterapia', 'Sesión de fisioterapia', 'Fisioterapia avanzada', 'Rehabilitación deportiva', 'Suelo pélvico', 'Magnetolith', 'Fisioterapia a domicilio'],
        professionals: ['Cualquier fisioterapeuta disponible', 'Manuel Cuenca', 'Fernando López', 'Álvaro Hurtado', 'Víctor González', 'Alex Velasco'],
    },
    {
        id: 'osteopatia',
        name: 'Osteopatía',
        description: 'Osteopatía general, avanzada, pediátrica, visceral, craneal y ATM.',
        enabled: true,
        icon: HeartPulse,
        services: ['Primera valoración de osteopatía', 'Sesión de osteopatía', 'Osteopatía pediátrica', 'Osteopatía ATM'],
        professionals: ['Cualquier osteópata disponible', 'Manuel Cuenca', 'Fernando López'],
    },
    {
        id: 'nutricion',
        name: 'Nutrición',
        description: 'Primera consulta y seguimiento nutricional personalizado.',
        enabled: true,
        icon: Salad,
        services: ['Primera consulta de nutrición', 'Revisión de nutrición'],
        professionals: ['Profesional de nutrición · por confirmar'],
    },
    {
        id: 'psicologia',
        name: 'Psicología',
        description: 'Atención psicológica y acompañamiento emocional.',
        enabled: true,
        icon: Brain,
        services: ['Primera consulta de psicología', 'Sesión de seguimiento'],
        professionals: ['Profesional de psicología · por confirmar'],
    },
    {
        id: 'entrenamiento',
        name: 'Entrenamiento personal',
        description: 'Planificación de entrenamiento y vuelta segura a la actividad.',
        enabled: false,
        icon: Dumbbell,
        services: ['Valoración de entrenamiento', 'Sesión de entrenamiento personal'],
        professionals: ['José David López'],
    },
];

const slots = ['08:30', '09:15', '10:30', '12:00', '16:15', '18:00', '19:30'];

export default function ManuelCuencaBooking() {
    const [departmentId, setDepartmentId] = useState('fisioterapia');
    const [service, setService] = useState('');
    const [professional, setProfessional] = useState('');
    const [time, setTime] = useState('');
    const [date, setDate] = useState('');
    const [submitted, setSubmitted] = useState(false);

    const department = useMemo(
        () => departments.find((item) => item.id === departmentId) ?? departments[0],
        [departmentId]
    );

    const selectDepartment = (id: string) => {
        setDepartmentId(id);
        setService('');
        setProfessional('');
        setTime('');
        setSubmitted(false);
    };

    if (submitted) {
        return (
            <main className="grid min-h-screen place-items-center bg-[#eef5ff] px-5 py-16 text-[#071753]">
                <section className="w-full max-w-2xl rounded-[2rem] bg-white p-8 text-center shadow-2xl sm:p-12">
                    <span className="mx-auto grid h-20 w-20 place-items-center rounded-full bg-[#dff8ed] text-[#1f9368]"><Check className="h-10 w-10" /></span>
                    <p className="mt-7 text-sm font-extrabold uppercase tracking-[0.2em] text-[#2f85e8]">Simulación completada</p>
                    <h1 className="mt-3 text-3xl font-black sm:text-4xl">Así verá el paciente su confirmación</h1>
                    <div className="mt-8 rounded-2xl bg-[#f7f9fc] p-6 text-left">
                        <p><strong>Área:</strong> {department.name}</p>
                        <p className="mt-2"><strong>Servicio:</strong> {service}</p>
                        <p className="mt-2"><strong>Profesional:</strong> {professional}</p>
                        <p className="mt-2"><strong>Hora elegida:</strong> {time}</p>
                        <p className="mt-2"><strong>Fecha elegida:</strong> {date}</p>
                    </div>
                    <div className="mt-6 flex items-start gap-3 rounded-2xl border border-[#2f85e8]/20 bg-[#eef5ff] p-4 text-left text-sm text-[#465173]">
                        <Info className="mt-0.5 h-5 w-5 shrink-0 text-[#2f85e8]" /> Esta candidata no escribe todavía en una agenda real. La conexión transaccional se incorporará después de validar servicios, profesionales y reglas con la clínica.
                    </div>
                    <div className="mt-8 flex flex-col justify-center gap-3 sm:flex-row">
                        <button onClick={() => setSubmitted(false)} className="min-h-12 rounded-full border border-[#071753]/15 px-6 font-bold">Cambiar selección</button>
                        <Link to="/" className="flex min-h-12 items-center justify-center rounded-full bg-[#2f85e8] px-6 font-bold text-white">Volver a la web</Link>
                    </div>
                </section>
            </main>
        );
    }

    const canSubmit = Boolean(service && professional && date && time);

    return (
        <div className="min-h-screen bg-[#f7f9fc] text-[#071753]">
            <header className="border-b border-[#071753]/10 bg-white">
                <div className="mx-auto flex min-h-20 max-w-7xl items-center justify-between px-5 sm:px-8">
                    <Link to="/" className="flex min-h-11 items-center gap-2 font-extrabold"><ArrowLeft className="h-5 w-5" /> Volver</Link>
                    <div className="text-right">
                        <p className="font-black">Reservar cita</p>
                        <p className="text-xs text-[#5d6682]">Demo Manuel Cuenca × Weedex</p>
                    </div>
                </div>
            </header>

            <main className="mx-auto max-w-7xl px-5 py-12 sm:px-8 lg:py-16">
                <div className="max-w-3xl">
                    <p className="text-sm font-extrabold uppercase tracking-[0.2em] text-[#2f85e8]">Disponibilidad compartida</p>
                    <h1 className="mt-3 text-4xl font-black sm:text-5xl">Encuentra la cita adecuada</h1>
                    <p className="mt-4 text-lg leading-relaxed text-[#5d6682]">Elige el área, el tratamiento y el profesional. Los datos pendientes aparecen señalados y no se presentan como confirmados.</p>
                </div>

                <section className="mt-10">
                    <h2 className="flex items-center gap-2 text-lg font-black"><span className="grid h-8 w-8 place-items-center rounded-full bg-[#2f85e8] text-sm text-white">1</span> Área asistencial</h2>
                    <div className="mt-5 grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
                        {departments.map((item) => {
                            const Icon = item.icon;
                            const selected = departmentId === item.id;
                            return (
                                <button key={item.id} disabled={!item.enabled} onClick={() => selectDepartment(item.id)} className={`relative min-h-44 rounded-2xl border p-5 text-left transition ${selected ? 'border-[#2f85e8] bg-[#eef5ff] shadow-lg' : 'border-[#071753]/10 bg-white hover:border-[#2f85e8]/50'} disabled:cursor-not-allowed disabled:opacity-55`}>
                                    <Icon className="h-6 w-6 text-[#2f85e8]" />
                                    <span className="mt-5 block font-black">{item.name}</span>
                                    <span className="mt-2 block text-xs leading-relaxed text-[#5d6682]">{item.description}</span>
                                    {!item.enabled && <span className="absolute right-3 top-3 rounded-full bg-amber-100 px-2 py-1 text-[10px] font-extrabold text-amber-800">POR CONFIRMAR</span>}
                                </button>
                            );
                        })}
                    </div>
                </section>

                <div className="mt-10 grid gap-8 lg:grid-cols-2">
                    <section className="rounded-[1.5rem] bg-white p-6 shadow-sm sm:p-8">
                        <h2 className="flex items-center gap-2 text-lg font-black"><span className="grid h-8 w-8 place-items-center rounded-full bg-[#2f85e8] text-sm text-white">2</span> Servicio</h2>
                        <div className="mt-5 grid gap-3">
                            {department.services.map((item) => (
                                <button key={item} onClick={() => { setService(item); setTime(''); }} className={`flex min-h-12 items-center justify-between rounded-xl border px-4 text-left font-semibold ${service === item ? 'border-[#2f85e8] bg-[#eef5ff] text-[#176cc9]' : 'border-[#071753]/10 hover:border-[#2f85e8]/40'}`}>
                                    {item} {service === item && <Check className="h-4 w-4" />}
                                </button>
                            ))}
                        </div>
                    </section>

                    <section className="rounded-[1.5rem] bg-white p-6 shadow-sm sm:p-8">
                        <h2 className="flex items-center gap-2 text-lg font-black"><span className="grid h-8 w-8 place-items-center rounded-full bg-[#2f85e8] text-sm text-white">3</span> Profesional</h2>
                        <div className="mt-5 grid gap-3">
                            {department.professionals.map((item) => (
                                <button key={item} onClick={() => { setProfessional(item); setTime(''); }} className={`flex min-h-12 items-center gap-3 rounded-xl border px-4 text-left font-semibold ${professional === item ? 'border-[#2f85e8] bg-[#eef5ff] text-[#176cc9]' : 'border-[#071753]/10 hover:border-[#2f85e8]/40'}`}>
                                    <UserRound className="h-4 w-4 shrink-0" /> {item}
                                </button>
                            ))}
                        </div>
                    </section>
                </div>

                <section className="mt-8 rounded-[1.5rem] bg-white p-6 shadow-sm sm:p-8">
                    <h2 className="flex items-center gap-2 text-lg font-black"><span className="grid h-8 w-8 place-items-center rounded-full bg-[#2f85e8] text-sm text-white">4</span> Fecha y hora</h2>
                    <div className="mt-6 grid gap-8 lg:grid-cols-[0.7fr_1.3fr]">
                        <div className="rounded-2xl bg-[#071753] p-6 text-white">
                            <CalendarDays className="h-7 w-7 text-[#72d7a8]" />
                            <label htmlFor="demo-date" className="mt-5 block text-sm text-white/80">Fecha de demostración</label>
                            <input id="demo-date" type="date" required value={date} onChange={(event) => { setDate(event.target.value); setTime(''); }} className="mt-3 min-h-12 w-full rounded-xl bg-white px-4 text-[#071753]" />
                            <p className="mt-4 text-xs leading-relaxed text-white/60">Los huecos son ficticios hasta conectar la agenda real.</p>
                        </div>
                        <div>
                            <p className="flex items-center gap-2 font-bold"><Clock3 className="h-5 w-5 text-[#2f85e8]" /> Horas disponibles</p>
                            <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
                                {slots.map((slot) => (
                                    <button key={slot} disabled={!service || !professional} onClick={() => setTime(slot)} className={`min-h-12 rounded-xl border font-extrabold ${time === slot ? 'border-[#2f85e8] bg-[#2f85e8] text-white' : 'border-[#071753]/10 hover:border-[#2f85e8]'} disabled:cursor-not-allowed disabled:opacity-35`}>{slot}</button>
                                ))}
                            </div>
                        </div>
                    </div>
                </section>

                <div className="mt-8 flex flex-col items-start justify-between gap-5 rounded-[1.5rem] bg-[#071753] p-6 text-white sm:flex-row sm:items-center sm:p-8">
                    <div className="flex items-start gap-3">
                        <ShieldCheck className="mt-1 h-6 w-6 shrink-0 text-[#72d7a8]" />
                        <div><p className="font-black">Modo demostración seguro</p><p className="mt-1 text-sm text-white/65">No se creará ninguna cita ni se enviará ninguna notificación.</p></div>
                    </div>
                    <button disabled={!canSubmit} onClick={() => setSubmitted(true)} className="flex min-h-14 w-full items-center justify-center gap-2 rounded-full bg-[#72d7a8] px-7 font-black text-[#071753] transition hover:bg-white disabled:cursor-not-allowed disabled:opacity-35 sm:w-auto">Simular confirmación <ArrowRight className="h-5 w-5" /></button>
                </div>
            </main>
        </div>
    );
}
