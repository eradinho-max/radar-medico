-- Radar Médico — schema definitivo de persistência
-- Preparado para Supabase/Postgres. Ainda não aplicado em produção.

create extension if not exists pgcrypto;

create table if not exists public.sources (
  id uuid primary key default gen_random_uuid(),
  slug text not null unique,
  name text not null,
  kind text not null check (kind in ('official','board','aggregator')),
  scope text not null,
  base_url text not null,
  enabled boolean not null default true,
  priority smallint not null default 100,
  adapter text not null,
  last_success_at timestamptz,
  last_error_at timestamptz,
  last_error text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.crawl_runs (
  id uuid primary key default gen_random_uuid(),
  source_id uuid references public.sources(id) on delete set null,
  started_at timestamptz not null default now(),
  finished_at timestamptz,
  status text not null check (status in ('running','success','partial','error')),
  discovered_count integer not null default 0,
  accepted_count integer not null default 0,
  rejected_count integer not null default 0,
  error_count integer not null default 0,
  meta jsonb not null default '{}'::jsonb
);

create table if not exists public.discovered_documents (
  id uuid primary key default gen_random_uuid(),
  source_id uuid references public.sources(id) on delete cascade,
  crawl_run_id uuid references public.crawl_runs(id) on delete set null,
  source_url text not null,
  canonical_url text not null,
  title text,
  content_hash text,
  discovered_at timestamptz not null default now(),
  last_seen_at timestamptz not null default now(),
  medical_candidate boolean not null default false,
  classification jsonb not null default '{}'::jsonb,
  unique(source_id, canonical_url)
);

create table if not exists public.opportunities (
  id uuid primary key default gen_random_uuid(),
  fingerprint text not null unique,
  title text not null,
  organization text,
  city text,
  state char(2),
  specialty text,
  specialties text[] not null default '{}',
  cargo text,
  salary numeric(14,2),
  workload text,
  vacancies text,
  reserve_list boolean not null default false,
  fee numeric(12,2),
  registration_start date,
  registration_deadline date,
  exam_date text,
  board text,
  modality text,
  status text not null default 'unknown',
  official_url text,
  source_url text,
  source_name text,
  source_type text not null check (source_type in ('official','board','aggregator')),
  edital_pdf text,
  first_seen_at timestamptz not null default now(),
  last_seen_at timestamptz not null default now(),
  last_changed_at timestamptz not null default now(),
  possible_revision_of uuid references public.opportunities(id) on delete set null,
  flags text[] not null default '{}',
  raw jsonb not null default '{}'::jsonb,
  active boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists opportunities_status_idx on public.opportunities(status);
create index if not exists opportunities_state_idx on public.opportunities(state);
create index if not exists opportunities_deadline_idx on public.opportunities(registration_deadline);
create index if not exists opportunities_source_type_idx on public.opportunities(source_type);
create index if not exists opportunities_specialties_gin_idx on public.opportunities using gin(specialties);

create table if not exists public.opportunity_versions (
  id uuid primary key default gen_random_uuid(),
  opportunity_id uuid not null references public.opportunities(id) on delete cascade,
  version_no integer not null,
  captured_at timestamptz not null default now(),
  snapshot jsonb not null,
  changed_fields text[] not null default '{}',
  source_url text,
  unique(opportunity_id, version_no)
);

create table if not exists public.alerts (
  id uuid primary key default gen_random_uuid(),
  email text not null,
  enabled boolean not null default true,
  query text,
  states text[] not null default '{}',
  specialties text[] not null default '{}',
  salary_min numeric(14,2),
  workload_max integer,
  modalities text[] not null default '{}',
  only_open boolean not null default true,
  immediate boolean not null default false,
  daily_digest boolean not null default true,
  revisions boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.alert_matches (
  id uuid primary key default gen_random_uuid(),
  alert_id uuid not null references public.alerts(id) on delete cascade,
  opportunity_id uuid not null references public.opportunities(id) on delete cascade,
  opportunity_version_id uuid references public.opportunity_versions(id) on delete set null,
  match_type text not null check (match_type in ('new','revision','deadline','digest')),
  matched_at timestamptz not null default now(),
  sent_at timestamptz,
  delivery_status text not null default 'pending',
  unique(alert_id, opportunity_id, opportunity_version_id, match_type)
);

-- Segurança: tabelas expostas em public ficam com RLS habilitado.
alter table public.sources enable row level security;
alter table public.crawl_runs enable row level security;
alter table public.discovered_documents enable row level security;
alter table public.opportunities enable row level security;
alter table public.opportunity_versions enable row level security;
alter table public.alerts enable row level security;
alter table public.alert_matches enable row level security;

-- Leitura pública somente das oportunidades publicáveis.
create policy "public can read active opportunities"
on public.opportunities
for select
to anon, authenticated
using (active = true and official_url is not null);

-- Nenhuma policy pública de escrita.
-- Coletores e rotas administrativas usarão credencial server-side secreta,
-- nunca exposta ao navegador.

comment on table public.opportunities is
'Fonte única de verdade das oportunidades médicas publicadas no Radar Médico.';

comment on column public.opportunities.official_url is
'Obrigatória para publicação pública; deve apontar para fonte oficial verificável.';

comment on column public.opportunities.source_type is
'Origem da descoberta. Aggregator pode descobrir, mas não substitui official_url.';
