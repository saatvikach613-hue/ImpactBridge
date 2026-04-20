with features as (
    select * from {{ ref('int_kid_features') }}
),

risk_scored as (
    select
        kid_id,
        chapter_id,
        kid_name,
        current_math_level,
        current_english_level,
        attendance_rate,
        avg_rating,
        consecutive_struggles,
        stuck_flag,
        days_since_last_session,
        volunteer_consistency,

        -- Risk score calculation (0-6 scale)
        (
            case when attendance_rate < 0.5         then 1 else 0 end +
            case when avg_rating < 1.5              then 1 else 0 end +
            case when consecutive_struggles >= 2    then 1 else 0 end +
            case when stuck_flag = 1                then 1 else 0 end +
            case when days_since_last_session > 14  then 1 else 0 end +
            case when volunteer_consistency < 0.5   then 1 else 0 end
        ) as risk_score_raw,

        case
            when (
                case when attendance_rate < 0.5         then 1 else 0 end +
                case when avg_rating < 1.5              then 1 else 0 end +
                case when consecutive_struggles >= 2    then 1 else 0 end +
                case when stuck_flag = 1                then 1 else 0 end +
                case when days_since_last_session > 14  then 1 else 0 end +
                case when volunteer_consistency < 0.5   then 1 else 0 end
            ) >= 3 then 'high'
            when (
                case when attendance_rate < 0.5         then 1 else 0 end +
                case when avg_rating < 1.5              then 1 else 0 end +
                case when consecutive_struggles >= 2    then 1 else 0 end +
                case when stuck_flag = 1                then 1 else 0 end +
                case when days_since_last_session > 14  then 1 else 0 end +
                case when volunteer_consistency < 0.5   then 1 else 0 end
            ) >= 2 then 'medium'
            else 'low'
        end as risk_level,

        case
            when (
                case when attendance_rate < 0.5         then 1 else 0 end +
                case when avg_rating < 1.5              then 1 else 0 end +
                case when consecutive_struggles >= 2    then 1 else 0 end +
                case when stuck_flag = 1                then 1 else 0 end +
                case when days_since_last_session > 14  then 1 else 0 end +
                case when volunteer_consistency < 0.5   then 1 else 0 end
            ) >= 2 then true
            else false
        end as at_risk

    from features
)

select * from risk_scored
order by risk_score_raw desc
