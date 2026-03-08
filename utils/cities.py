from dataclasses import dataclass


@dataclass(frozen=True)
class City:
    name: str
    lat: float
    lng: float
    province: str
    region: str


CITIES: dict[str, City] = {
    "torino":    City("Torino",    45.0703, 7.6869,   "TO", "Piemonte"),
    "milano":    City("Milano",    45.4654, 9.1859,   "MI", "Lombardia"),
    "brescia":   City("Brescia",   45.5416, 10.2118,  "BS", "Lombardia"),
    "bergamo":   City("Bergamo",   45.6983, 9.6773,   "BG", "Lombardia"),
    "monza":     City("Monza",     45.5845, 9.2744,   "MB", "Lombardia"),
    "como":      City("Como",      45.8080, 9.0852,   "CO", "Lombardia"),
    "varese":    City("Varese",    45.8206, 8.8257,   "VA", "Lombardia"),
    "pavia":     City("Pavia",     45.1847, 9.1582,   "PV", "Lombardia"),
    "cremona":   City("Cremona",   45.1333, 10.0333,  "CR", "Lombardia"),
    "mantova":   City("Mantova",   45.1564, 10.7913,  "MN", "Lombardia"),
    "cesano":    City("Cesano Maderno", 45.62915, 9.15189, "CM", "Lombardia"),
    "genova":    City("Genova",    44.4056, 8.9463,   "GE", "Liguria"),

    "verona":    City("Verona",    45.4384, 10.9916,  "VR", "Veneto"),
    "venezia":   City("Venezia",   45.4408, 12.3155,  "VE", "Veneto"),
    "padova":    City("Padova",    45.4064, 11.8768,  "PD", "Veneto"),
    "vicenza":   City("Vicenza",   45.5455, 11.5354,  "VI", "Veneto"),
    "treviso":   City("Treviso",   45.6669, 12.2430,  "TV", "Veneto"),
    "trento":    City("Trento",    46.0748, 11.1217,  "TN", "Trentino-Alto Adige"),
    "bolzano":   City("Bolzano",   46.4983, 11.3548,  "BZ", "Trentino-Alto Adige"),
    "trieste":   City("Trieste",   45.6495, 13.7768,  "TS", "Friuli-Venezia Giulia"),
    "udine":     City("Udine",     46.0633, 13.2350,  "UD", "Friuli-Venezia Giulia"),
    "bologna":   City("Bologna",   44.4949, 11.3426,  "BO", "Emilia-Romagna"),
    "modena":    City("Modena",    44.6471, 10.9252,  "MO", "Emilia-Romagna"),
    "parma":     City("Parma",     44.8015, 10.3279,  "PR", "Emilia-Romagna"),
    "ferrara":   City("Ferrara",   44.8381, 11.6197,  "FE", "Emilia-Romagna"),
    "piacenza":  City("Piacenza",  45.0526, 9.6930,   "PC", "Emilia-Romagna"),
    "reggio_emilia": City("Reggio Emilia", 44.6989, 10.6297, "RE", "Emilia-Romagna"),

    "firenze":   City("Firenze",   43.7696, 11.2558,  "FI", "Toscana"),
    "pisa":      City("Pisa",      43.7228, 10.4017,  "PI", "Toscana"),
    "siena":     City("Siena",     43.3186, 11.3307,  "SI", "Toscana"),
    "livorno":   City("Livorno",   43.5485, 10.3106,  "LI", "Toscana"),
    "perugia":   City("Perugia",   43.1107, 12.3908,  "PG", "Umbria"),
    "ancona":    City("Ancona",    43.6158, 13.5189,  "AN", "Marche"),
    "roma":      City("Roma",      41.9028, 12.4964,  "RM", "Lazio"),
    "latina":    City("Latina",    41.4677, 12.9035,  "LT", "Lazio"),

    "napoli":    City("Napoli",    40.8518, 14.2681,  "NA", "Campania"),
    "salerno":   City("Salerno",   40.6824, 14.7681,  "SA", "Campania"),
    "bari":      City("Bari",      41.1171, 16.8719,  "BA", "Puglia"),
    "taranto":   City("Taranto",   40.4668, 17.2470,  "TA", "Puglia"),
    "foggia":    City("Foggia",    41.4621, 15.5444,  "FG", "Puglia"),
    "potenza":   City("Potenza",   40.6396, 15.8056,  "PZ", "Basilicata"),
    "catanzaro": City("Catanzaro", 38.9100, 16.5877,  "CZ", "Calabria"),
    "reggio_calabria": City("Reggio Calabria", 38.1113, 15.6474, "RC", "Calabria"),

    "palermo":   City("Palermo",   38.1157, 13.3615,  "PA", "Sicilia"),
    "catania":   City("Catania",   37.5079, 15.0830,  "CT", "Sicilia"),
    "messina":   City("Messina",   38.1938, 15.5540,  "ME", "Sicilia"),
    "cagliari":  City("Cagliari",  39.2238, 9.1217,   "CA", "Sardegna"),
    "sassari":   City("Sassari",   40.7259, 8.5557,   "SS", "Sardegna"),
}