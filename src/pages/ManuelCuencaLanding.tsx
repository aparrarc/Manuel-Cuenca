import { useState } from 'react';
import { Link } from 'react-router-dom';
import {
    Activity,
    ArrowRight,
    Brain,
    CalendarDays,
    CheckCircle2,
    Dumbbell,
    HeartPulse,
    Home,
    Mail,
    MapPin,
    Menu,
    Phone,
    Salad,
    Syringe,
    X,
} from 'lucide-react';
import { getBrandConfig } from '../config/brandConfig';

const brand = getBrandConfig();
const logoUrl = 'https://www.manuelcuencafisioterapia.com/wp-content/uploads/2021/09/Manuel-cuenca.svg';

const serviceIcons = [Activity, HeartPulse, Syringe, Salad, Brain, Home];

export default function ManuelCuencaLanding() {
    const [menuOpen, setMenuOpen] = useState(false);

    return (
        <div className="min-h-screen bg-[#f7f9fc] text-[#071753] selection:bg-[#2f85e8]/20">
            <header className="sticky top-0 z-50 border-b border-[#071753]/10 bg-white/95 backdrop-blur">
                <div className="bg-[#071753] text-white">
                    <div className="mx-auto flex max-w-7xl items-center justify-between px-5 py-2 text-xs sm:px-8">
                        <a className="flex min-h-11 items-center gap-2 hover:text-[#72d7a8]" href={`tel:${brand.contactPhone.replace(/\s/g, '')}`}>
                            <Phone className="h-4 w-4" /> {brand.contactPhone}
                        </a>
                        <span className="hidden text-white/75 sm:block">L–V · 08:00–22:00 · Sábados con cita previa</span>
                    </div>
                </div>
                <nav className="mx-auto flex min-h-20 max-w-7xl items-center justify-between px-5 sm:px-8">
                    <a href="#inicio" aria-label="Manuel Cuenca Fisioterapia" className="shrink-0">
                        <img src={logoUrl} alt="Manuel Cuenca Fisioterapia" className="h-11 w-auto sm:h-13" />
                    </a>
                    <div className="hidden items-center gap-7 text-sm font-semibold lg:flex">
                        <a href="#servicios" className="hover:text-[#2f85e8]">Especialidades</a>
                        <a href="#equipo" className="hover:text-[#2f85e8]">Equipo</a>
                        <a href="#clinica" className="hover:text-[#2f85e8]">Clínica</a>
                        <a href="#contacto" className="hover:text-[#2f85e8]">Contacto</a>
                    </div>
                    <div className="flex items-center gap-2">
                        <Link to="/booking" className="hidden min-h-11 items-center gap-2 rounded-full bg-[#2f85e8] px-5 text-sm font-bold text-white shadow-lg shadow-blue-300/30 transition hover:bg-[#176cc9] sm:flex">
                            <CalendarDays className="h-4 w-4" /> Reservar cita
                        </Link>
                        <button onClick={() => setMenuOpen((open) => !open)} className="grid min-h-11 min-w-11 place-items-center rounded-full border border-[#071753]/15 lg:hidden" aria-label="Abrir menú">
                            {menuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
                        </button>
                    </div>
                </nav>
                {menuOpen && (
                    <div className="border-t border-[#071753]/10 bg-white px-5 py-4 lg:hidden">
                        {['servicios', 'equipo', 'clinica', 'contacto'].map((item) => (
                            <a key={item} href={`#${item}`} onClick={() => setMenuOpen(false)} className="block min-h-11 py-3 font-semibold capitalize">{item}</a>
                        ))}
                        <Link to="/booking" className="mt-3 flex min-h-12 items-center justify-center rounded-full bg-[#2f85e8] font-bold text-white">Reservar cita</Link>
                    </div>
                )}
            </header>

            <main>
                <section id="inicio" className="relative overflow-hidden bg-[#071753] text-white">
                    <div className="absolute inset-0 opacity-15 [background-image:radial-gradient(circle_at_20%_20%,#2f85e8_0,transparent_35%),radial-gradient(circle_at_80%_80%,#72d7a8_0,transparent_30%)]" />
                    <div className="relative mx-auto grid min-h-[670px] max-w-7xl items-center gap-12 px-5 py-16 sm:px-8 lg:grid-cols-[0.9fr_1.1fr] lg:py-20">
                        <div className="max-w-2xl">
                            <p className="mb-5 text-sm font-bold uppercase tracking-[0.22em] text-[#72d7a8]">Clínica de fisioterapia en Málaga</p>
                            <h1 className="text-5xl font-black leading-[0.98] sm:text-6xl lg:text-7xl">
                                Recuperamos<br /><span className="text-[#72d7a8]">tu mejor tú</span>
                            </h1>
                            <p className="mt-7 max-w-xl text-lg leading-relaxed text-white/78 sm:text-xl">{brand.heroDescription}</p>
                            <div className="mt-9 flex flex-col gap-3 sm:flex-row">
                                <Link to="/booking" className="flex min-h-14 items-center justify-center gap-2 rounded-full bg-[#72d7a8] px-7 font-extrabold text-[#071753] transition hover:bg-white">
                                    Consultar disponibilidad <ArrowRight className="h-5 w-5" />
                                </Link>
                                <a href={`tel:${brand.contactPhone.replace(/\s/g, '')}`} className="flex min-h-14 items-center justify-center gap-2 rounded-full border border-white/35 px-7 font-bold transition hover:bg-white/10">
                                    <Phone className="h-5 w-5" /> Llamar ahora
                                </a>
                            </div>
                            <div className="mt-8 flex flex-wrap gap-x-6 gap-y-3 text-sm text-white/75">
                                <span className="flex items-center gap-2"><CheckCircle2 className="h-4 w-4 text-[#72d7a8]" /> Equipo multidisciplinar</span>
                                <span className="flex items-center gap-2"><CheckCircle2 className="h-4 w-4 text-[#72d7a8]" /> Reserva online 24/7</span>
                            </div>
                        </div>
                        <div className="relative">
                            <div className="absolute -inset-5 rotate-2 rounded-[2.5rem] bg-[#2f85e8]/35" />
                            <img src={brand.heroImages[0]} alt="Equipo de Manuel Cuenca Fisioterapia" className="relative h-[420px] w-full rounded-[2rem] object-cover object-center shadow-2xl sm:h-[520px]" />
                            <div className="absolute -bottom-5 left-4 rounded-2xl bg-white p-4 text-[#071753] shadow-xl sm:left-8 sm:p-5">
                                <p className="text-xs font-bold uppercase tracking-wider text-[#2f85e8]">Atención continuada</p>
                                <p className="mt-1 font-extrabold">Lunes a viernes · 08:00–22:00</p>
                            </div>
                        </div>
                    </div>
                </section>

                <section id="servicios" className="mx-auto max-w-7xl px-5 py-20 sm:px-8 lg:py-28">
                    <div className="grid gap-10 lg:grid-cols-[0.75fr_1.25fr] lg:items-end">
                        <div>
                            <p className="text-sm font-extrabold uppercase tracking-[0.2em] text-[#2f85e8]">Especialidades</p>
                            <h2 className="mt-4 text-4xl font-black leading-tight sm:text-5xl">¿Qué podemos hacer por ti?</h2>
                        </div>
                        <p className="max-w-2xl text-lg leading-relaxed text-[#465173]">Un enfoque integral para recuperar autonomía, calidad de vida y salud. La agenda final mostrará sólo los tratamientos que el centro confirme como reservables online.</p>
                    </div>
                    <div className="mt-12 grid gap-5 md:grid-cols-2 lg:grid-cols-3">
                        {brand.services.map((service, index) => {
                            const Icon = serviceIcons[index] ?? Activity;
                            return (
                                <article key={service.id} className="group overflow-hidden rounded-[1.5rem] border border-[#071753]/10 bg-white shadow-sm transition hover:-translate-y-1 hover:shadow-xl">
                                    <div className="relative h-52 overflow-hidden">
                                        {index === 0 ? (
                                            <img src={service.image} alt={service.name} className="h-full w-full object-cover transition duration-700 group-hover:scale-105" loading="lazy" />
                                        ) : (
                                            <div className="grid h-full place-items-center bg-[#eaf2fc] text-[#2f85e8]"><Icon className="h-20 w-20" aria-hidden="true" /></div>
                                        )}
                                        <div className="absolute inset-0 bg-gradient-to-t from-[#071753]/55 to-transparent" />
                                        <span className="absolute bottom-4 left-4 grid h-11 w-11 place-items-center rounded-full bg-white text-[#2f85e8] shadow-lg"><Icon className="h-5 w-5" /></span>
                                    </div>
                                    <div className="p-6">
                                        <h3 className="text-xl font-black">{service.name}</h3>
                                        <p className="mt-3 min-h-18 text-sm leading-relaxed text-[#5d6682]">{service.description}</p>
                                        <Link to="/booking" className="mt-5 inline-flex min-h-11 items-center gap-2 font-extrabold text-[#2f85e8]">Ver citas <ArrowRight className="h-4 w-4" /></Link>
                                    </div>
                                </article>
                            );
                        })}
                    </div>
                </section>

                <section id="equipo" className="bg-[#eaf2fc] py-20 lg:py-28">
                    <div className="mx-auto max-w-7xl px-5 sm:px-8">
                        <div className="max-w-3xl">
                            <p className="text-sm font-extrabold uppercase tracking-[0.2em] text-[#2f85e8]">Cuadro técnico</p>
                            <h2 className="mt-4 text-4xl font-black sm:text-5xl">Tu salud, en buenas manos</h2>
                            <p className="mt-5 text-lg leading-relaxed text-[#465173]">Profesionales especializados que trabajan de forma coordinada para encontrar el tratamiento adecuado.</p>
                        </div>
                        <div className="mt-12 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
                            {brand.team.map((member) => (
                                <article key={member.name} className="overflow-hidden rounded-[1.5rem] bg-white shadow-sm">
                                    <img src={member.image} alt={member.name} className="h-72 w-full object-cover object-top" loading="lazy" />
                                    <div className="p-6">
                                        <h3 className="text-xl font-black">{member.name}</h3>
                                        <p className="mt-2 text-sm font-semibold leading-relaxed text-[#2f85e8]">{member.specialty}</p>
                                    </div>
                                </article>
                            ))}
                        </div>
                    </div>
                </section>

                <section id="clinica" className="mx-auto grid max-w-7xl gap-12 px-5 py-20 sm:px-8 lg:grid-cols-2 lg:items-center lg:py-28">
                    <div className="grid grid-cols-2 gap-3">
                        {brand.galleryImages.slice(0, 4).map((src, index) => (
                            <img key={src} src={src} alt={`Instalaciones Manuel Cuenca ${index + 1}`} className={`w-full rounded-2xl object-cover ${index % 2 ? 'mt-8 h-56' : 'h-64'}`} loading="lazy" />
                        ))}
                    </div>
                    <div>
                        <p className="text-sm font-extrabold uppercase tracking-[0.2em] text-[#2f85e8]">La clínica</p>
                        <h2 className="mt-4 text-4xl font-black leading-tight sm:text-5xl">Cuidamos cada parte de tu recuperación</h2>
                        <p className="mt-6 text-lg leading-relaxed text-[#465173]">Fisioterapia, osteopatía, rehabilitación y salud integral en un espacio pensado para acompañarte desde la primera valoración hasta tu vuelta a la actividad.</p>
                        <div className="mt-8 grid gap-4 sm:grid-cols-2">
                            <div className="rounded-2xl bg-[#f0f7f4] p-5"><HeartPulse className="h-6 w-6 text-[#2b9b70]" /><p className="mt-3 font-extrabold">Plan personalizado</p></div>
                            <div className="rounded-2xl bg-[#eef5ff] p-5"><Dumbbell className="h-6 w-6 text-[#2f85e8]" /><p className="mt-3 font-extrabold">Recuperación activa</p></div>
                        </div>
                    </div>
                </section>

                <section className="bg-[#2f85e8] px-5 py-16 text-white sm:px-8">
                    <div className="mx-auto flex max-w-7xl flex-col items-start justify-between gap-8 lg:flex-row lg:items-center">
                        <div>
                            <p className="text-sm font-bold uppercase tracking-[0.2em] text-white/70">Una única disponibilidad</p>
                            <h2 className="mt-3 max-w-3xl text-3xl font-black sm:text-4xl">Reserva por web, teléfono o recepción sin perder el control de la agenda.</h2>
                        </div>
                        <Link to="/booking" className="flex min-h-14 shrink-0 items-center gap-2 rounded-full bg-white px-7 font-extrabold text-[#071753] shadow-xl">Reservar cita <ArrowRight className="h-5 w-5" /></Link>
                    </div>
                </section>
            </main>

            <footer id="contacto" className="bg-[#071753] text-white">
                <div className="mx-auto grid max-w-7xl gap-10 px-5 py-14 sm:px-8 md:grid-cols-3">
                    <div>
                        <img src={logoUrl} alt="Manuel Cuenca Fisioterapia" className="h-13 w-auto brightness-0 invert" />
                        <p className="mt-5 max-w-sm text-sm leading-relaxed text-white/65">Tu clínica de fisioterapia y osteopatía en Málaga, especializada en recuperar y hacer crecer la salud de las personas.</p>
                    </div>
                    <div>
                        <h3 className="font-black">Contacto</h3>
                        <div className="mt-4 space-y-3 text-sm text-white/72">
                            <a href={`tel:${brand.contactPhone.replace(/\s/g, '')}`} className="flex min-h-11 items-center gap-3 hover:text-white"><Phone className="h-4 w-4" /> {brand.contactPhone}</a>
                            <a href={`mailto:${brand.contactEmail}`} className="flex min-h-11 items-center gap-3 hover:text-white"><Mail className="h-4 w-4" /> {brand.contactEmail}</a>
                            <p className="flex items-start gap-3"><MapPin className="mt-1 h-4 w-4 shrink-0" /> {brand.contactAddress}</p>
                        </div>
                    </div>
                    <div>
                        <h3 className="font-black">Horario</h3>
                        <p className="mt-4 text-sm leading-7 text-white/72">Lunes a viernes: 08:00–22:00<br />Sábados: con cita previa</p>
                    </div>
                </div>
                <div className="border-t border-white/10 px-5 py-5 text-center text-xs text-white/45">Demo personalizada Weedex · Contenido e identidad visual de Manuel Cuenca Fisioterapia</div>
            </footer>
        </div>
    );
}
