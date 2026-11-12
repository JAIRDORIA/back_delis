-- ============================================================================
-- SnackFlow / Delis  ->  Compras con categoria y venta ligada
-- Motor: MySQL 8.x (Clever Cloud).  NO MariaDB.
-- ----------------------------------------------------------------------------
-- ORDEN DE EJECUCION
--   1) Correr la seccion "MIGRACION" en la BD de PRUEBA y verificar con los
--      SELECT de "COMPROBACION".
--   2) Correr la MISMA seccion "MIGRACION" en PRODUCCION.
--   3) SOLO DESPUES desplegar el backend nuevo (el codigo lee estas columnas;
--      si se despliega antes, POST/GET /compras/ y /cortes/balance fallan).
-- ----------------------------------------------------------------------------
-- QUE HACE
--   compras.categoria  ENUM('insumo','domicilio') NOT NULL DEFAULT 'insumo'
--                      -> todas las compras existentes quedan 'insumo'.
--   compras.venta_id   INT NULL
--                      -> solo se usa cuando categoria = 'domicilio'.
--   Indices: idx_compras_categoria, idx_compras_venta.
-- ----------------------------------------------------------------------------
-- NOTAS
--   * Idempotente: cada ALTER se ejecuta solo si la columna/indice no existe.
--   * No se agrega FOREIGN KEY a ventas(id): no se pudo verificar desde el
--     repo el tipo exacto de ventas.id (INT vs INT UNSIGNED vs BIGINT) y una FK
--     con tipo distinto falla. La integridad se valida en el service:
--     la venta debe existir, no estar anulada y tener valor_domicilio > 0.
--   * No hay backfill que recalcular: el DEFAULT 'insumo' ya llena las filas
--     existentes (se incluye un UPDATE defensivo por si la columna llegara a
--     existir nullable de una corrida parcial).
--   * Los cortes ya cerrados NO se recalculan: cerrar_corte() solo cambia
--     estados y el balance se calcula al vuelo.
-- ============================================================================

-- ---------------------------------------------------------------------------
-- MIGRACION
-- ---------------------------------------------------------------------------
DELIMITER $$

DROP PROCEDURE IF EXISTS snackflow_mig_compras_domicilio $$
CREATE PROCEDURE snackflow_mig_compras_domicilio()
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME   = 'compras'
          AND COLUMN_NAME  = 'categoria'
    ) THEN
        ALTER TABLE compras
            ADD COLUMN categoria ENUM('insumo','domicilio') NOT NULL DEFAULT 'insumo'
            AFTER descripcion;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME   = 'compras'
          AND COLUMN_NAME  = 'venta_id'
    ) THEN
        ALTER TABLE compras
            ADD COLUMN venta_id INT NULL DEFAULT NULL
            AFTER categoria;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.STATISTICS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME   = 'compras'
          AND INDEX_NAME   = 'idx_compras_categoria'
    ) THEN
        ALTER TABLE compras ADD INDEX idx_compras_categoria (categoria);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.STATISTICS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME   = 'compras'
          AND INDEX_NAME   = 'idx_compras_venta'
    ) THEN
        ALTER TABLE compras ADD INDEX idx_compras_venta (venta_id);
    END IF;
END $$

DELIMITER ;

CALL snackflow_mig_compras_domicilio();

DROP PROCEDURE snackflow_mig_compras_domicilio;

-- Backfill defensivo (no hace nada si la columna ya es NOT NULL y tiene default)
UPDATE compras SET categoria = 'insumo' WHERE categoria IS NULL;

-- ---------------------------------------------------------------------------
-- COMPROBACION (correr despues de la migracion; todo debe salir OK)
-- ---------------------------------------------------------------------------
-- 1) Columnas creadas
SELECT COLUMN_NAME, COLUMN_TYPE, IS_NULLABLE, COLUMN_DEFAULT
FROM information_schema.COLUMNS
WHERE TABLE_SCHEMA = DATABASE()
  AND TABLE_NAME   = 'compras'
  AND COLUMN_NAME IN ('categoria','venta_id');

-- 2) Indices creados
SELECT INDEX_NAME, COLUMN_NAME
FROM information_schema.STATISTICS
WHERE TABLE_SCHEMA = DATABASE()
  AND TABLE_NAME   = 'compras'
  AND INDEX_NAME IN ('idx_compras_categoria','idx_compras_venta');

-- 3) Ninguna compra existente quedo fuera de categoria (debe devolver 0)
SELECT COUNT(*) AS compras_sin_categoria FROM compras WHERE categoria IS NULL;

-- 4) Ninguna compra 'insumo' quedo con venta_id (debe devolver 0)
SELECT COUNT(*) AS insumos_con_venta FROM compras
WHERE categoria = 'insumo' AND venta_id IS NOT NULL;

-- 5) Reparto actual (informativo)
SELECT categoria, COUNT(*) AS cantidad, COALESCE(SUM(total), 0) AS total
FROM compras
WHERE eliminada = 0
GROUP BY categoria;

-- ---------------------------------------------------------------------------
-- ROLLBACK  (ejecutar SOLO si hay que revertir el backend anterior)
-- El backend viejo ignora las columnas, asi que el rollback es opcional y solo
-- se hace si se quiere dejar la tabla exactamente como estaba.
-- ---------------------------------------------------------------------------
-- ALTER TABLE compras DROP INDEX idx_compras_venta;
-- ALTER TABLE compras DROP COLUMN venta_id;
-- ALTER TABLE compras DROP INDEX idx_compras_categoria;
-- ALTER TABLE compras DROP COLUMN categoria;
--
-- Verificacion del rollback (ambas deben devolver 0 filas):
-- SELECT COLUMN_NAME FROM information_schema.COLUMNS
--  WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'compras'
--    AND COLUMN_NAME IN ('categoria','venta_id');
