const MEDICAL_TERMS = [
  "médico","medico","medicina","psiquiatra","psiquiatria","geriatra","geriatria",
  "clínico","clinico","clínica médica","clinica medica","generalista",
  "medicina de família","medicina de familia","médico da família","medico da familia",
  "esf","médico do trabalho","medico do trabalho","medicina do trabalho",
  "plantonista","regulador","perito médico","perito medico","anestesiologista",
  "cardiologista","pediatra","ginecologista","obstetra","radiologista","cirurgião",
  "cirurgiao","infectologista","neurologista","nefrologista","oncologista"
];

const OPPORTUNITY_TERMS = [
  "concurso","processo seletivo","seleção","selecao","edital","provimento",
  "contratação","contratacao","cadastro reserva","vaga","vagas"
];

function normalize(value: string) {
  return value.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase();
}

export function classifyMedicalOpportunity(text: string) {
  const normalized = normalize(text);
  const medicalHits = MEDICAL_TERMS.filter(term => normalized.includes(normalize(term)));
  const opportunityHits = OPPORTUNITY_TERMS.filter(term => normalized.includes(normalize(term)));
  return {
    isMedical: medicalHits.length > 0 && opportunityHits.length > 0,
    medicalHits: Array.from(new Set(medicalHits)),
    opportunityHits: Array.from(new Set(opportunityHits))
  };
}
