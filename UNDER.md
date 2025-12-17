Plan: Add Explanations for Attention Rates
Problem
Users are confused about why attention rates appear low (~47%). They need clarification on:

What "tiene_atencion" actually means
Why some radicados don't have attention
Whether this is normal or indicates a problem
Analysis Findings
From data analysis:

47.1% of radicados have id_atencion (8,426 of 17,904)
Key pattern: ALL radicados with attention have servicio defined
Key pattern: ALL radicados without attention have NO servicio defined
Radicados without attention include: internal documents, responses, administrative processes, pending cases
Solution: Add Explanatory Content
1. Add Information Box in KPIs Section
Location: After the KPI metrics in proyectos/analisis_radicados.py

Add an expandable info box explaining:

What "tiene_atencion" means (radicado linked to a service/attention record)
Why some radicados don't have attention (pending, administrative, responses, etc.)
That this is normal workflow behavior
2. Add Contextual Insights Section
Location: In the main analysis tab "Por Mes y Canal de Ingreso"

Add a collapsible section with:

Explanation of the attention rate
Breakdown showing relationship between servicio and tiene_atencion
Examples of common radicados without attention
Interpretation guidance
3. Add Tooltips/Help Text
Location: Near key metrics and charts

Add help icons or tooltips explaining:

What "Tasa de Atención" means
The difference between "Con Atención" and "Sin Atención"
When a radicado gets an id_atencion
4. Add Analysis Section
Location: New subsection in "Resumen Ejecutivo" tab

Add analysis showing:

Patterns of which radicados get attention
Common types of radicados without attention
Time-based patterns (recent vs older radicados)
Implementation Details
Files to Modify
proyectos/analisis_radicados.py
Code Changes
After KPIs section (around line 180):
with st.expander("ℹ️ ¿Qué significa 'Tiene Atención'?"):
    st.markdown("""
    **Definición:** Un radicado "tiene atención" cuando ha sido procesado y vinculado 
    a un registro de servicio/atención en el sistema (tiene un `id_atencion` asignado).
    
    **¿Por qué algunos radicados no tienen atención?**
    - Documentos administrativos internos que no requieren atención directa
    - Respuestas a otras entidades
    - Casos pendientes de procesamiento
    - Procesos administrativos que no generan atención registrada
    
    **Nota:** Es normal que no todos los radicados tengan atención, ya que muchos 
    son documentos administrativos o procesos internos.
    """)
In main analysis tab (after the main table):
Add an insights section explaining patterns

In Resumen Ejecutivo tab:
Add analysis of attention patterns

Benefits
Users understand what the metrics mean
Reduces confusion about "low" attention rates
Provides context for interpretation
Helps users make informed decisions based on the data