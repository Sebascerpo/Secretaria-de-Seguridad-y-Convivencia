source .venv/bin/activate && pip install -r requirements.txt && streamlit run main.py


audiencias
SELECT
    v.fecha_audiencia::date AS fecha_audiencia,
    v.juzgado AS juzgado,
    v.funcion_audiencia AS tipo_proceso,        -- CONOCIMIENTO / GARANTÍAS
    v.tipo_audiencia AS clase_audiencia,        -- Legalización, Acusación, etc.
    v.nunc_cui_spoa AS radicado,
    v.delito_penal AS delito,
    v.delegado AS delegado,
    v.rol_audiencia AS rol,                     -- Víctima / Detenido / Otro
    v.observaciones AS observaciones,
    CONCAT_WS(' ', v.nombres, v.apellidos) AS nombre_persona, -- segura con NULL
    v.sexo AS sexo,
    v.pais AS pais
FROM vista_asistencia_juzgados_detalle v
WHERE v.fecha_audiencia BETWEEN '2025-01-1' AND '2025-12-30'
ORDER BY v.fecha_audiencia ASC, v.juzgado, v.tipo_audiencia;