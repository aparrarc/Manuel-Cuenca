export const inputClass = 'mt-2 min-h-12 w-full rounded-xl border border-blue-200 bg-white px-3 text-[#071753]';
export const madridDate = () => new Intl.DateTimeFormat('en-CA', { timeZone: 'Europe/Madrid' }).format(new Date());
export const clock = (value: string) => new Date(value).toLocaleTimeString('es-ES', { timeZone: 'Europe/Madrid', hour: '2-digit', minute: '2-digit' });
export const appointmentDate = (value: string) => new Date(value).toLocaleString('es-ES', { timeZone: 'Europe/Madrid', dateStyle: 'medium', timeStyle: 'short' });
