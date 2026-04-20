with session_logs as (
    select * from {{ ref('stg_session_logs') }}
),

kids as (
    select * from {{ ref('stg_kids') }}
),

rsvps as (
    select * from {{ ref('stg_rsvps') }}
),

-- Last 4 weeks of logs per kid
recent_logs as (
    select *
    from session_logs
    where logged_at >= current_timestamp - interval '4 weeks'
),

-- Attendance rate per kid
attendance as (
    select
        kid_id,
        count(distinct session_id)::float /
            nullif(count(distinct session_id), 0) as attendance_rate,
        count(distinct session_id) as sessions_attended
    from recent_logs
    group by kid_id
),

-- Average rating and trend per kid
ratings as (
    select
        kid_id,
        avg(rating_num)                         as avg_rating,
        count(*) filter (where rating = 'struggling') as struggle_count,
        max(logged_at)                          as last_session_at
    from recent_logs
    group by kid_id
),

-- Stuck flag — same chapter 3+ times
stuck as (
    select
        kid_id,
        case
            when count(distinct chapter_covered) = 1
             and count(*) >= 3
            then 1 else 0
        end as stuck_flag
    from (
        select kid_id, chapter_covered
        from session_logs
        order by logged_at desc
        limit 3
    ) last_3
    group by kid_id
),

-- Volunteer consistency per kid
vol_consistency as (
    select
        vka.kid_id,
        avg(r.confirmed_flag::float) as volunteer_consistency
    from {{ source('impactbridge', 'volunteer_kid_assignments') }} vka
    join rsvps r on r.volunteer_id = vka.volunteer_id
    where vka.is_active = true
    group by vka.kid_id
),

-- Chapters per month (learning velocity)
velocity as (
    select
        kid_id,
        case
            when max(logged_at) > min(logged_at)
            then (max(chapter_covered) - min(chapter_covered))::float /
                 nullif(
                     extract(epoch from max(logged_at) - min(logged_at)) / 2592000,
                     0
                 )
            else 0.5
        end as chapters_per_month
    from session_logs
    group by kid_id
)

select
    k.kid_id,
    k.chapter_id,
    k.kid_name,
    k.current_math_level,
    k.current_english_level,
    case k.current_english_level
        when 'letter'   then 0
        when 'word'     then 1
        when 'sentence' then 2
        when 'story'    then 3
        when 'advanced' then 4
        else 0
    end as current_english_level_num,
    case k.current_math_level
        when 'pre_number'           then 0
        when 'number_recognition'   then 1
        when 'basic_operations'     then 2
        when 'advanced_operations'  then 3
        when 'syllabus_aligned'     then 4
        else 2
    end as current_math_level_num,
    k.learning_style,
    k.interests,
    coalesce(a.attendance_rate, 0)                              as attendance_rate,
    coalesce(r.avg_rating, 2.0)                                 as avg_rating,
    coalesce(r.struggle_count, 0)                               as consecutive_struggles,
    coalesce(v.chapters_per_month, 0.5)                         as chapters_per_month,
    coalesce(
        extract(epoch from current_timestamp - r.last_session_at) / 86400,
        30
    )::int                                                      as days_since_last_session,
    coalesce(vc.volunteer_consistency, 1.0)                     as volunteer_consistency,
    coalesce(s.stuck_flag, 0)                                   as stuck_flag
from kids k
left join attendance  a  on a.kid_id  = k.kid_id
left join ratings     r  on r.kid_id  = k.kid_id
left join stuck       s  on s.kid_id  = k.kid_id
left join vol_consistency vc on vc.kid_id = k.kid_id
left join velocity    v  on v.kid_id  = k.kid_id
