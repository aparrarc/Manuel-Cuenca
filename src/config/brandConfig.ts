// Configuración única de la demo pública de Manuel Cuenca.
// Repositorio independiente: únicamente contiene la marca Manuel Cuenca.
import manuelCuencaConfig from './brands/manuelcuenca';

export interface ServiceItem { id: number; name: string; duration: string; description: string; price: string; image: string; emoji?: string; }
export interface TeamMember { name: string; specialty: string; quote: string; image: string; }
export interface Testimonial { quote: string; author: string; role: string; }
export interface BrandTheme { cssClass: string; accent: string; mode: 'dark' | 'light'; }
export interface BrandTerminology { professional: string; professionals: string; establishment: string; bookingStep: string; }
export interface BrandConfig {
    id: string; name: string; tagline: string; subtitle: string; heroHeadline: string; heroDescription: string;
    ctaText: string; contactEmail: string; contactPhone: string; contactAddress: string; heroImages: string[];
    services: ServiceItem[]; team: TeamMember[]; testimonials: Testimonial[]; galleryImages: string[];
    theme: BrandTheme; terminology: BrandTerminology; logoIcon: string; copyright: string;
}

export const BRAND_ID = 'manuelcuenca' as const;

/** La demo siempre utiliza la identidad de Manuel Cuenca. */
export function getBrandConfig(): BrandConfig { return manuelCuencaConfig; }

/** Inicializa únicamente metadatos locales, sin red ni loaders de marcas. */
export function initBrand(): BrandConfig {
    document.documentElement.classList.add(`theme-${manuelCuencaConfig.theme.cssClass}`);
    document.documentElement.lang = 'es';
    document.title = manuelCuencaConfig.name;
    return manuelCuencaConfig;
}
