with features as (
    select * from {{ ref('int_kid_features') }}
),

resource_needs as (
    select
        kid_id,
        chapter_id,
        kid_name,
        current_math_level,
        current_english_level,
        chapters_per_month,

        case current_math_level
            when 'pre_number'           then 'Pre-number activity kit (counting, sorting)'
            when 'number_recognition'   then 'Number recognition workbook (1-100)'
            when 'basic_operations'     then 'Basic operations workbook (add, subtract, multiply)'
            when 'advanced_operations'  then 'Advanced math workbook (fractions, decimals)'
            when 'syllabus_aligned'     then 'School syllabus math workbook'
            else null
        end as math_resource_needed,

        case current_english_level
            when 'letter'   then 'Phonics & alphabet flashcard set'
            when 'word'     then 'Word building & reading cards'
            when 'sentence' then 'Sentence construction workbook'
            when 'story'    then 'Story books — Telugu & English (set of 5)'
            when 'advanced' then 'Advanced reading comprehension book'
            else null
        end as english_resource_needed,

        stuck_flag,
        learning_style

    from features
)

select
    kid_id,
    chapter_id,
    kid_name,
    math_resource_needed,
    english_resource_needed,
    case when stuck_flag = 1 then 'Math activity kit' else null end as supplementary_resource,
    current_date + interval '4 weeks' as predicted_need_date
from resource_needs
where
    math_resource_needed is not null
    or english_resource_needed is not null
    or stuck_flag = 1
order by chapter_id, kid_id
