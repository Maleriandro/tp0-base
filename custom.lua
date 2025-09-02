local p_custom = Proto("custom", "Custom Protocol")

local f_tipo = ProtoField.uint8("custom.tipo", "Tipo de mensaje", base.DEC)

-- ENVIO_BATCH
local f_id_agencia   = ProtoField.uint32("custom.envio_batch.id_agencia", "ID Agencia", base.DEC)
local f_num_apuestas = ProtoField.uint8("custom.envio_batch.num_apuestas", "Número de apuestas", base.DEC)
local f_nombre       = ProtoField.string("custom.envio_batch.nombre", "Nombre")
local f_apellido     = ProtoField.string("custom.envio_batch.apellido", "Apellido")
local f_dni          = ProtoField.uint32("custom.envio_batch.dni", "DNI", base.DEC)
local f_cumple       = ProtoField.string("custom.envio_batch.cumple", "Cumpleaños")
local f_numero       = ProtoField.uint32("custom.envio_batch.numero", "Número", base.DEC)

-- CONFIRMACION_RECEPCION
local f_conf = ProtoField.uint8("custom.confirmacion", "Confirmación", base.DEC)

-- SOLICITUD_GANADORES
local f_solicitud_id = ProtoField.uint32("custom.solicitud.id_agencia", "ID Agencia", base.DEC)

-- RESPUESTA_GANADORES
local f_cant_ganadores = ProtoField.uint32("custom.respuesta.cant", "Cantidad de ganadores", base.DEC)
local f_dni_ganador    = ProtoField.uint32("custom.respuesta.dni", "DNI Ganador", base.DEC)

p_custom.fields = {
    f_tipo,
    f_id_agencia, f_num_apuestas, f_nombre, f_apellido, f_dni, f_cumple, f_numero,
    f_conf,
    f_solicitud_id,
    f_cant_ganadores, f_dni_ganador
}

-- Helper: lee stringz con límite de longitud
local function read_stringz_bounded(buffer, offset, max_len)
    if offset >= buffer:len() then return nil, offset, 0 end
    local remaining = buffer:len() - offset
    local limit = math.min(max_len, remaining)
    local nul_at = nil
    for i = 0, limit - 1 do
        if buffer(offset + i, 1):uint() == 0 then
            nul_at = i
            break
        end
    end
    local str, consumed
    if nul_at ~= nil then
        str = buffer(offset, nul_at):string()
        consumed = nul_at + 1
    else
        str = buffer(offset, limit):string()
        consumed = limit
    end
    return str, offset + consumed, consumed
end

-- Función principal
function p_custom.dissector(buffer, pinfo, tree)
    if buffer:len() < 1 then return end

    pinfo.cols.protocol = "CUSTOM"

    local tipo = buffer(0,1):uint()
    local subtree = tree:add(p_custom, buffer(), "Custom Protocol Data")
    subtree:add(f_tipo, buffer(0,1))

    local offset = 1

    if tipo == 1 then
        pinfo.cols.info = "ENVIO_BATCH"

        -- id_agencia
        if offset + 4 > buffer:len() then return end
        subtree:add(f_id_agencia, buffer(offset,4))
        offset = offset + 4

        -- num_apuestas
        if offset + 1 > buffer:len() then return end
        local num_apuestas = buffer(offset,1):uint()
        subtree:add(f_num_apuestas, buffer(offset,1))
        offset = offset + 1

        -- Apuestas
        for i = 1, num_apuestas do
            if offset >= buffer:len() then break end

            local apuesta_tree = subtree:add(p_custom, buffer(offset), "Apuesta " .. i)

            -- nombre (stringz, max 30)
            local s_off = offset
            local nombre, new_off, consumed = read_stringz_bounded(buffer, offset, 30)
            if nombre ~= nil and consumed > 0 then
                apuesta_tree:add(f_nombre, buffer(s_off, consumed))
                offset = new_off
            end

            -- apellido (stringz, max 30)
            s_off = offset
            local apellido, new_off, consumed = read_stringz_bounded(buffer, offset, 30)
            if apellido ~= nil and consumed > 0 then
                apuesta_tree:add(f_apellido, buffer(s_off, consumed))
                offset = new_off
            end

            -- dni (4 bytes)
            if offset + 4 <= buffer:len() then
                apuesta_tree:add(f_dni, buffer(offset,4))
                offset = offset + 4
            else break end

            -- cumple (stringz, max 11)
            s_off = offset
            local cumple, new_off, consumed = read_stringz_bounded(buffer, offset, 11)
            if cumple ~= nil and consumed > 0 then
                apuesta_tree:add(f_cumple, buffer(s_off, consumed))
                offset = new_off
            end

            -- numero (4 bytes)
            if offset + 4 <= buffer:len() then
                apuesta_tree:add(f_numero, buffer(offset,4))
                offset = offset + 4
            else break end
        end

    elseif tipo == 2 then
        pinfo.cols.info = "CONFIRMACION_RECEPCION"
        if offset + 1 <= buffer:len() then
            subtree:add(f_conf, buffer(offset,1))
        end

    elseif tipo == 3 then
        pinfo.cols.info = "SOLICITUD_GANADORES"
        if offset + 4 <= buffer:len() then
            subtree:add(f_solicitud_id, buffer(offset,4))
        end

    elseif tipo == 4 then
        pinfo.cols.info = "SORTEO_NO_REALIZADO"
        -- sin body

    elseif tipo == 5 then
        pinfo.cols.info = "RESPUESTA_GANADORES"
        if offset + 4 <= buffer:len() then
            local cant = buffer(offset,4):uint()
            subtree:add(f_cant_ganadores, buffer(offset,4))
            offset = offset + 4

            for i=1,cant do
                if offset + 4 > buffer:len() then break end
                subtree:add(f_dni_ganador, buffer(offset,4))
                offset = offset + 4
            end
        end
    else
        pinfo.cols.info = "Tipo desconocido ("..tipo..")"
    end
end

-- Registramos el puerto
DissectorTable.get("tcp.port"):add(12345, p_custom)

