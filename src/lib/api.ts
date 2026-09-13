export type Professional = { id: string; name: string; role: string };
export type Service = { id: string; name: string; department: string; duration: number; professionalIds: string[] };
export type Department = { id: string; name: string; enabled: boolean };
export type Slot = { professionalId: string; start: string; end: string };
export type Booking = { id: string; serviceId: string; professionalId: string; start: string; end: string; customerName: string; phone: string; status: string };
export type Catalog = { professionals: Professional[]; services: Service[]; departments: Department[]; demo: boolean; whatsappEnabled?: boolean };

async function request<T>(path: string, init?: RequestInit): Promise<T> {
    const response = await fetch(path, { ...init, headers: { 'Content-Type': 'application/json', ...(init?.headers ?? {}) } });
    if (!response.ok) {
        const body = await response.json().catch(() => ({}));
        const message = response.status === 409 ? 'El hueco ha cambiado o está ocupado. Consulta de nuevo la disponibilidad.' : response.status === 401 ? 'Acceso no autorizado. Comprueba tu sesión o contraseña.' : response.status === 429 ? 'Demasiadas solicitudes. Espera un minuto.' : body?.message || body?.error?.message || `No se pudo completar la solicitud (${response.status})`;
        throw new Error(typeof message === 'string' ? message : 'No se pudo completar la solicitud');
    }
    return response.json() as Promise<T>;
}

export const api = {
    catalog: () => request<Catalog>('/api/catalog'),
    availability: (serviceId: string, date: string, professionalId?: string, signal?: AbortSignal) => request<{ slots: Slot[] }>(`/api/availability?serviceId=${encodeURIComponent(serviceId)}&date=${encodeURIComponent(date)}${professionalId ? `&professionalId=${encodeURIComponent(professionalId)}` : ''}`, { signal }),
    createBooking: (body: { serviceId: string; professionalId: string; start: string; customerName: string; phone: string; idempotencyKey: string; whatsappConsent?: boolean }) => request<{ booking: Booking; managementToken: string; whatsapp?: {status: string} }>('/api/bookings', { method: 'POST', body: JSON.stringify(body) }),
    getBooking: (id: string, token: string) => request<{ booking: Booking }>(`/api/bookings/${encodeURIComponent(id)}`, { headers: { 'X-Management-Token': token } }),
    updateBooking: (id: string, token: string, body: { start: string; professionalId: string; idempotencyKey: string }) => request<{ booking: Booking }>(`/api/bookings/${encodeURIComponent(id)}`, { method: 'PATCH', headers: { 'X-Management-Token': token }, body: JSON.stringify(body) }),
    cancelBooking: (id: string, token?: string) => request<{ booking: Booking }>(`/api/bookings/${encodeURIComponent(id)}`, { method: 'DELETE', ...(token ? { headers: { 'X-Management-Token': token } } : {}) }),
    adminLogin: (password: string) => request<{ ok: boolean }>('/api/admin/login', { method: 'POST', body: JSON.stringify({ password }) }),
    adminLogout: () => request<{ ok: boolean }>('/api/admin/logout', { method: 'POST' }),
    adminSession: () => request<{ authenticated: boolean }>('/api/admin/session'),
    adminBookings: (date: string, professionalId?: string) => request<{ bookings: Booking[] }>(`/api/admin/bookings?date=${encodeURIComponent(date)}${professionalId ? `&professionalId=${encodeURIComponent(professionalId)}` : ''}`),
};

export const managementKey = 'manuel-cuenca-demo-reservations';
export type SavedReservation = { id: string; token: string };
export function savedReservations(): SavedReservation[] { try { return JSON.parse(sessionStorage.getItem(managementKey) || '[]'); } catch { return []; } }
export function saveReservation(value: SavedReservation) { sessionStorage.setItem(managementKey, JSON.stringify([value, ...savedReservations().filter((item) => item.id !== value.id)])); }
