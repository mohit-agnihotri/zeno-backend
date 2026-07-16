-- Create a function to search for jobs by vector similarity
create or replace function match_jobs (
  query_embedding vector(384),
  match_threshold float,
  match_count int
)
returns table (
  id uuid,
  title text,
  company text,
  city text,
  job_type text,
  source_url text,
  description text,
  posted_at timestamp with time zone,
  similarity float
)
language sql stable
as $$
  select
    jobs.id,
    jobs.title,
    jobs.company,
    jobs.city,
    jobs.job_type,
    jobs.source_url,
    jobs.description,
    jobs.posted_at,
    1 - (jobs.job_vector <=> query_embedding) as similarity
  from jobs
  where jobs.is_spam = false
  and 1 - (jobs.job_vector <=> query_embedding) > match_threshold
  order by jobs.job_vector <=> query_embedding
  limit match_count;
$$;
