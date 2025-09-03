# TP0: Docker + Comunicaciones + Concurrencia

En el presente repositorio se provee un esqueleto básico de cliente/servidor, en donde todas las dependencias del mismo se encuentran encapsuladas en containers. Los alumnos deberán resolver una guía de ejercicios incrementales, teniendo en cuenta las condiciones de entrega descritas al final de este enunciado.

 El cliente (Golang) y el servidor (Python) fueron desarrollados en diferentes lenguajes simplemente para mostrar cómo dos lenguajes de programación pueden convivir en el mismo proyecto con la ayuda de containers, en este caso utilizando [Docker Compose](https://docs.docker.com/compose/).

## Instrucciones de uso
El repositorio cuenta con un **Makefile** que incluye distintos comandos en forma de targets. Los targets se ejecutan mediante la invocación de:  **make \<target\>**. Los target imprescindibles para iniciar y detener el sistema son **docker-compose-up** y **docker-compose-down**, siendo los restantes targets de utilidad para el proceso de depuración.

Los targets disponibles son:

| target  | accion  |
|---|---|
|  `docker-compose-up`  | Inicializa el ambiente de desarrollo. Construye las imágenes del cliente y el servidor, inicializa los recursos a utilizar (volúmenes, redes, etc) e inicia los propios containers. |
| `docker-compose-down`  | Ejecuta `docker-compose stop` para detener los containers asociados al compose y luego  `docker-compose down` para destruir todos los recursos asociados al proyecto que fueron inicializados. Se recomienda ejecutar este comando al finalizar cada ejecución para evitar que el disco de la máquina host se llene de versiones de desarrollo y recursos sin liberar. |
|  `docker-compose-logs` | Permite ver los logs actuales del proyecto. Acompañar con `grep` para lograr ver mensajes de una aplicación específica dentro del compose. |
| `docker-image`  | Construye las imágenes a ser utilizadas tanto en el servidor como en el cliente. Este target es utilizado por **docker-compose-up**, por lo cual se lo puede utilizar para probar nuevos cambios en las imágenes antes de arrancar el proyecto. |
| `build` | Compila la aplicación cliente para ejecución en el _host_ en lugar de en Docker. De este modo la compilación es mucho más veloz, pero requiere contar con todo el entorno de Golang y Python instalados en la máquina _host_. |

### Servidor

Se trata de un "echo server", en donde los mensajes recibidos por el cliente se responden inmediatamente y sin alterar. 

Se ejecutan en bucle las siguientes etapas:

1. Servidor acepta una nueva conexión.
2. Servidor recibe mensaje del cliente y procede a responder el mismo.
3. Servidor desconecta al cliente.
4. Servidor retorna al paso 1.


### Cliente
 se conecta reiteradas veces al servidor y envía mensajes de la siguiente forma:
 
1. Cliente se conecta al servidor.
2. Cliente genera mensaje incremental.
3. Cliente envía mensaje al servidor y espera mensaje de respuesta.
4. Servidor responde al mensaje.
5. Servidor desconecta al cliente.
6. Cliente verifica si aún debe enviar un mensaje y si es así, vuelve al paso 2.

### Ejemplo

Al ejecutar el comando `make docker-compose-up`  y luego  `make docker-compose-logs`, se observan los siguientes logs:

```
client1  | 2024-08-21 22:11:15 INFO     action: config | result: success | client_id: 1 | server_address: server:12345 | loop_amount: 5 | loop_period: 5s | log_level: DEBUG
client1  | 2024-08-21 22:11:15 INFO     action: receive_message | result: success | client_id: 1 | msg: [CLIENT 1] Message N°1
server   | 2024-08-21 22:11:14 DEBUG    action: config | result: success | port: 12345 | listen_backlog: 5 | logging_level: DEBUG
server   | 2024-08-21 22:11:14 INFO     action: accept_connections | result: in_progress
server   | 2024-08-21 22:11:15 INFO     action: accept_connections | result: success | ip: 172.25.125.3
server   | 2024-08-21 22:11:15 INFO     action: receive_message | result: success | ip: 172.25.125.3 | msg: [CLIENT 1] Message N°1
server   | 2024-08-21 22:11:15 INFO     action: accept_connections | result: in_progress
server   | 2024-08-21 22:11:20 INFO     action: accept_connections | result: success | ip: 172.25.125.3
server   | 2024-08-21 22:11:20 INFO     action: receive_message | result: success | ip: 172.25.125.3 | msg: [CLIENT 1] Message N°2
server   | 2024-08-21 22:11:20 INFO     action: accept_connections | result: in_progress
client1  | 2024-08-21 22:11:20 INFO     action: receive_message | result: success | client_id: 1 | msg: [CLIENT 1] Message N°2
server   | 2024-08-21 22:11:25 INFO     action: accept_connections | result: success | ip: 172.25.125.3
server   | 2024-08-21 22:11:25 INFO     action: receive_message | result: success | ip: 172.25.125.3 | msg: [CLIENT 1] Message N°3
client1  | 2024-08-21 22:11:25 INFO     action: receive_message | result: success | client_id: 1 | msg: [CLIENT 1] Message N°3
server   | 2024-08-21 22:11:25 INFO     action: accept_connections | result: in_progress
server   | 2024-08-21 22:11:30 INFO     action: accept_connections | result: success | ip: 172.25.125.3
server   | 2024-08-21 22:11:30 INFO     action: receive_message | result: success | ip: 172.25.125.3 | msg: [CLIENT 1] Message N°4
server   | 2024-08-21 22:11:30 INFO     action: accept_connections | result: in_progress
client1  | 2024-08-21 22:11:30 INFO     action: receive_message | result: success | client_id: 1 | msg: [CLIENT 1] Message N°4
server   | 2024-08-21 22:11:35 INFO     action: accept_connections | result: success | ip: 172.25.125.3
server   | 2024-08-21 22:11:35 INFO     action: receive_message | result: success | ip: 172.25.125.3 | msg: [CLIENT 1] Message N°5
client1  | 2024-08-21 22:11:35 INFO     action: receive_message | result: success | client_id: 1 | msg: [CLIENT 1] Message N°5
server   | 2024-08-21 22:11:35 INFO     action: accept_connections | result: in_progress
client1  | 2024-08-21 22:11:40 INFO     action: loop_finished | result: success | client_id: 1
client1 exited with code 0
```


## Parte 1: Introducción a Docker
En esta primera parte del trabajo práctico se plantean una serie de ejercicios que sirven para introducir las herramientas básicas de Docker que se utilizarán a lo largo de la materia. El entendimiento de las mismas será crucial para el desarrollo de los próximos TPs.

### Ejercicio N°1:
Definir un script de bash `generar-compose.sh` que permita crear una definición de Docker Compose con una cantidad configurable de clientes.  El nombre de los containers deberá seguir el formato propuesto: client1, client2, client3, etc. 

El script deberá ubicarse en la raíz del proyecto y recibirá por parámetro el nombre del archivo de salida y la cantidad de clientes esperados:

`./generar-compose.sh docker-compose-dev.yaml 5`

Considerar que en el contenido del script pueden invocar un subscript de Go o Python:

```
#!/bin/bash
echo "Nombre del archivo de salida: $1"
echo "Cantidad de clientes: $2"
python3 mi-generador.py $1 $2
```

En el archivo de Docker Compose de salida se pueden definir volúmenes, variables de entorno y redes con libertad, pero recordar actualizar este script cuando se modifiquen tales definiciones en los sucesivos ejercicios.

>
>#### Resolucion:
>Para resolver este ejercicio implemente un script en bash, `generar-compose.sh`, que reciba como parámetros el nombre del archivo de salida y la cantidad de clientes. 
>El script primero checkea que los parametros sean correctos.
Luego, usa el comando cat para poder redirigir el contenido de un string al archivo indicado.
>Para tener multiples clientes, simplemnte se realiza un bucle donde se ejecuta cat una vez para cada cliente con su respectivo ID, apendeando el contenido al archivo creado.


### Ejercicio N°2:
Modificar el cliente y el servidor para lograr que realizar cambios en el archivo de configuración no requiera reconstruír las imágenes de Docker para que los mismos sean efectivos. La configuración a través del archivo correspondiente (`config.ini` y `config.yaml`, dependiendo de la aplicación) debe ser inyectada en el container y persistida por fuera de la imagen (hint: `docker volumes`).

> #### Resolución:
> Para resolver este ejercicio, se debe agregar al script que genera el compose, la definicion de volumenes que mapeen la configuracion encontrada en el repositorio, a la ubicacion dentro del docker. Para que cualquier cambio hecho en el host-os, se vea reflejado en el contenedor.
> Tambien fue necesario eliminar las variables de entorno `LOGGING_LEVEL` y `CLI_LOG_LEVEL` que generaban conflicto con los archivos de configuracion, para esa configuracion específica.

### Ejercicio N°3:
Crear un script de bash `validar-echo-server.sh` que permita verificar el correcto funcionamiento del servidor utilizando el comando `netcat` para interactuar con el mismo. Dado que el servidor es un echo server, se debe enviar un mensaje al servidor y esperar recibir el mismo mensaje enviado.

En caso de que la validación sea exitosa imprimir: `action: test_echo_server | result: success`, de lo contrario imprimir:`action: test_echo_server | result: fail`.

El script deberá ubicarse en la raíz del proyecto. Netcat no debe ser instalado en la máquina _host_ y no se pueden exponer puertos del servidor para realizar la comunicación (hint: `docker network`). `

> #### Resolución:
> Cree el script indicado. En el script, lanzo un nuevo contenedor de docker, indicandole la network a la que se tiene que conectar. Este contenedor es a partir de la imagen busybox que es una imagen chica que contiene netcat.
> Envio por netcat el mensaje al servidor y espero a recibirlo. (El contenedor se cierra automaticamente luego).
> Finalmente imprimo lo pedido por el ejercicio, y hago exit, con distintos valores para exito y error.


### Ejercicio N°4:
Modificar servidor y cliente para que ambos sistemas terminen de forma _graceful_ al recibir la signal SIGTERM. Terminar la aplicación de forma _graceful_ implica que todos los _file descriptors_ (entre los que se encuentran archivos, sockets, threads y procesos) deben cerrarse correctamente antes que el thread de la aplicación principal muera. Loguear mensajes en el cierre de cada recurso (hint: Verificar que hace el flag `-t` utilizado en el comando `docker compose down`).

> #### Resolución:
> Para parar tanto el cliente como el servidor, modifique el loop principal de ambos programas. Agregando un booleano, para terminar el loop de ejecucion.
> Cuando se recibe la señal, se setea este booleano para terminar el loop, y se cierra el socket (el unico en el caso de cliente, y el socket listen, y el del cliente en el caso del servidor).

## Parte 2: Repaso de Comunicaciones

Las secciones de repaso del trabajo práctico plantean un caso de uso denominado **Lotería Nacional**. Para la resolución de las mismas deberá utilizarse como base el código fuente provisto en la primera parte, con las modificaciones agregadas en el ejercicio 4.

### Ejercicio N°5:
Modificar la lógica de negocio tanto de los clientes como del servidor para nuestro nuevo caso de uso.

#### Cliente
Emulará a una _agencia de quiniela_ que participa del proyecto. Existen 5 agencias. Deberán recibir como variables de entorno los campos que representan la apuesta de una persona: nombre, apellido, DNI, nacimiento, numero apostado (en adelante 'número'). Ej.: `NOMBRE=Santiago Lionel`, `APELLIDO=Lorca`, `DOCUMENTO=30904465`, `NACIMIENTO=1999-03-17` y `NUMERO=7574` respectivamente.

Los campos deben enviarse al servidor para dejar registro de la apuesta. Al recibir la confirmación del servidor se debe imprimir por log: `action: apuesta_enviada | result: success | dni: ${DNI} | numero: ${NUMERO}`.



#### Servidor
Emulará a la _central de Lotería Nacional_. Deberá recibir los campos de la cada apuesta desde los clientes y almacenar la información mediante la función `store_bet(...)` para control futuro de ganadores. La función `store_bet(...)` es provista por la cátedra y no podrá ser modificada por el alumno.
Al persistir se debe imprimir por log: `action: apuesta_almacenada | result: success | dni: ${DNI} | numero: ${NUMERO}`.

#### Comunicación:
Se deberá implementar un módulo de comunicación entre el cliente y el servidor donde se maneje el envío y la recepción de los paquetes, el cual se espera que contemple:
* Definición de un protocolo para el envío de los mensajes.
* Serialización de los datos.
* Correcta separación de responsabilidades entre modelo de dominio y capa de comunicación.
* Correcto empleo de sockets, incluyendo manejo de errores y evitando los fenómenos conocidos como [_short read y short write_](https://cs61.seas.harvard.edu/site/2018/FileDescriptors/).

>#### Resolución:
>Para la resolución de este ejercicio, cree un modulo nuevo de comunicacion para tanto el cliente como el servidor.
>Este modulo se encarga de abstraer tanto el protocolo como serializacion para ambos ejecutables del proyecto.
>En particular, el protocolo consta de 2 mensajes:
>
>1. **Mensaje de Apuesta**: Contiene todos los datos de la apuesta (id agencia, nombre, apellido, DNI, nacimiento, número). Es el mensaje que envia el cliente, para informarle al servidor la nueva apuesta.
>2. **Mensaje de Confirmación**: Respuesta del servidor indicando si la apuesta fue recibida y almacenada correctamente.
>
>En particular se serializan de la siguiente manera:
>- Mensaje de apuesta:
>```
>| id_agencia (4bytes big-endian)|
>| len nombre (1byte)            | nombre (ascii var)     |
>| len apellido (1byte)          | apellido (ascii var)   |
>| DNI (4bytes big-endian)       |
>| len cumpleaños (1byte)        | cumpleaños (ascii var) |
>| numero (4bytes big-endian)    |
>```
>- Mensaje de confirmación:
>```
>| result (1byte)                | 
>```
>Siendo este `byte = 0`, en caso de exito, y otro entero en caso de error.
>
> Para enviar apuestas, primero el cliente debe conectarse al servidor. Una vez conectado, puede enviarle una unica apuesta, y esperar a la confirmación del cliente. Una vez confirmada la apuesta, la conexion es completada, y tanto el cliente como servidor se desconectan de este socket.
> Si se desea enviar nuevas apuestas, se debe iniciar una nueva conexion.
> Esto es así, para permitir que multiples clientes envien sus apuestas, sin tener que esperar necesariamente a que otro cliente envie la enteridad de sus propias apuestas, ya que el servidor solo puede atender un cliente a la vez.
>
>Para prevenir short-write y short read, para ambos modulos de comunicacion, implementé funciones de lectura y/o escritura, que aseguren la completitud del mensaje. Esto es: cada vez que hago un write o read, me fijo si recibí todos los bytes esperados. En el caso de no haberlo hecho, hago de nuevo la llamada (tenidneo en cuenta que tengo que ya no tengo que pedir los bytes que ya recibí).
>
>> En particular, python ya implementa una funcion sendall, por lo que la version de send en el servidor no es necesario implementarla.


### Ejercicio N°6:
Modificar los clientes para que envíen varias apuestas a la vez (modalidad conocida como procesamiento por _chunks_ o _batchs_). 
Los _batchs_ permiten que el cliente registre varias apuestas en una misma consulta, acortando tiempos de transmisión y procesamiento.

La información de cada agencia será simulada por la ingesta de su archivo numerado correspondiente, provisto por la cátedra dentro de `.data/datasets.zip`.
Los archivos deberán ser inyectados en los containers correspondientes y persistido por fuera de la imagen (hint: `docker volumes`), manteniendo la convencion de que el cliente N utilizara el archivo de apuestas `.data/agency-{N}.csv` .

En el servidor, si todas las apuestas del *batch* fueron procesadas correctamente, imprimir por log: `action: apuesta_recibida | result: success | cantidad: ${CANTIDAD_DE_APUESTAS}`. En caso de detectar un error con alguna de las apuestas, debe responder con un código de error a elección e imprimir: `action: apuesta_recibida | result: fail | cantidad: ${CANTIDAD_DE_APUESTAS}`.

La cantidad máxima de apuestas dentro de cada _batch_ debe ser configurable desde config.yaml. Respetar la clave `batch: maxAmount`, pero modificar el valor por defecto de modo tal que los paquetes no excedan los 8kB. 

Por su parte, el servidor deberá responder con éxito solamente si todas las apuestas del _batch_ fueron procesadas correctamente.

> #### Resoución:
> Para poder enviar más de un bet en un mensaje de apuesta, modifico ligeramente el protocolo, y el formato del mensaje.
> Se mantiene el protocolo, en el sentido de que primero se envia un mensaje de apuesta (que ahora puede contener más de una apuesta), y luego el servidor responde con 1 byte indicando exito u error.
> El cliente puede enviar un unico mensaje de apuestas por conexion.
>
> El mensaje de apuesta se modifica, no solo para poder enviar muchas bets en un unico mensaje, sino para achicar el tamaño maximo posible de una bet en particular, así poder incluir más bets en un unico mensaje sin superar los 8kb.
>
>```
>| id_agencia (4bytes big-endian)        |
>| numero de apuestas (1byte)            |  max 99
>| ------------------------------------- |
>| len nombre (null terminated string)   |  max 30 chars, including null
>| len apellido (null terminated string) |  max 30 chars, including null
>| DNI (4bytes big-endian)               |
>| cumpleaños (null terminated string)   |  max 11 chars, including null
>| numero (4bytes big-endian)            |
>```
>
>Con este nuevo formato, cada apuesta puede ocupar como máximo 30+30+4+11+4 = 79 bytes.
>Por lo que podemos obtener la cantidad máxima de apuestas que se pueden enviar en un único mensaje. 8000 bytes / 79 bytes ≈ 101 apuestas = 7979 bytes. Por lo que puedo enviar por batch 101 apuestas, ya que me queda suficiente espacio como para mandar el header.
>
> Similar al ejercicio anterior, el cliente puede enviar un unico batch de apuestas por cada conexion. Para permitir que otros clientes intercalen sus batches, y evitar que un cliente tenga que esperar demasiado a que otro cliente termine.
>
> Para agregar la data de apuestas, se agrega un nuevo punto de montaje en el script que genera los compose, tomando el argency-{id}.csv correspondiente, y montandolo en la raiz.
>
> Para leer las apuestas, implementé un struct `BetBatchReader`. Este struct abre el archivo CSV y permite leerlo de a batches, procesando y enviando cada lote de apuestas a medida que se lee. El archivo se cierra automáticamente al finalizar la lectura. Así, el cliente nunca tiene todas las apuestas en memoria, sino solo el batch actual.
>
> En el modulo de comunicacion, agregue la opcion de conectar y desconectrse del servidor, usado para conectarse antes de enviar cada batch, y desconectarse al recibir la confirmación de éxito.
>
>> Aclaracion:
>> Por alguna razon, en alguna de las ejecuciones de los test, si bien el programa cliente llegaba a la linea justo anterior a donde se ejecutraba os.Exit(n), el cliente no pareciera cerrarse de verdad, y el test termina esperando infinitamente la terminacion del cliente.
>> Por eso agregué prints de action exit, para que el test pueda finalizar, aunque el cliente no pareciera hacerlo.

### Ejercicio N°7:

Modificar los clientes para que notifiquen al servidor al finalizar con el envío de todas las apuestas y así proceder con el sorteo.
Inmediatamente después de la notificacion, los clientes consultarán la lista de ganadores del sorteo correspondientes a su agencia.
Una vez el cliente obtenga los resultados, deberá imprimir por log: `action: consulta_ganadores | result: success | cant_ganadores: ${CANT}`.

El servidor deberá esperar la notificación de las 5 agencias para considerar que se realizó el sorteo e imprimir por log: `action: sorteo | result: success`.
Luego de este evento, podrá verificar cada apuesta con las funciones `load_bets(...)` y `has_won(...)` y retornar los DNI de los ganadores de la agencia en cuestión. Antes del sorteo no se podrán responder consultas por la lista de ganadores con información parcial.

Las funciones `load_bets(...)` y `has_won(...)` son provistas por la cátedra y no podrán ser modificadas por el alumno.

No es correcto realizar un broadcast de todos los ganadores hacia todas las agencias, se espera que se informen los DNIs ganadores que correspondan a cada una de ellas.

> #### Resolución
> Para esta parte, se tiene que modificar nuevamente el protocolo.
> Como minimo deben agregarse 4 mensajes.
> - Uno que indique que el cliente terminó de enviar todas las apuestas. En este caso decidí que el cliente envie un batch de tamaño 0.
> - Uno para que el cliente solicite la lista de ganadores.
> - Uno para que el servidor informe la lista de ganadores.
> - Uno para que el servidor informe que el sorteo no fue realizado.
>
> Para agregar estos tipos de mensajes, decido agregarle a todos los mensajes un header de 1byte, seguido de un body, de la siguiente manera
> ```
> | tipo_mensaje (1byte)                 |
> | -------------------------------------|
> | body (ver más abajo)                 |
> ```
>
> Los valores para el tipo de mensaje, y como serían sus bodys, se describen a continuacion:
>
> ENVIO_BATCH = 1
>```
>| id_agencia (4bytes big-endian)        |
>| numero de apuestas (1byte)            |  max 99. 0 en caso de que no haya más apuestas.
>| ------------------------------------- |
>| nombre (null terminated string)       |  max 30 chars, including null
>| apellido (null terminated string)     |  max 30 chars, including null
>| DNI (4bytes big-endian)               |
>| cumpleaños (null terminated string)   |  max 11 chars, including null
>| numero (4bytes big-endian)            |
>```
>
> CONFIRMACION_RECEPCION = 2
> ```
> | confirmacion (1byte)                 | 0 en caso de exito, 1 en caso de error
> ```
>
> SOLICITUD_GANADORES = 3
> ```
> | id_agencia (4bytes big-endian)        |
> ```
>
> SORTEO_NO_REALIZADO = 4
> no tiene ningun body.
> 
> RESPUESTA_GANADORES = 5
> | cant_ganadores (4bytes big-endian) |
> | ---------------------------------- |
> | DNI ganador 1 (4bytes big-endian)  |
> |               (...)                |
> | DNI ganador N (4bytes big-endian)  |
>
> Para simplificar el protocolo, tambien decidí que el cliente envie todos los batchs en la misma conexion. En vez de utilizar una conexion para cada batch enviado.
>
>
> El flujo sería entonces:
> 1. El cliente se conecta al servidor
> 2. El cliente envía un batch de tamaño > 0
> 3. El servidor responde con una confirmación
> 5. Si el cliente tiene más apuestas, puede volver al paso 1.
> 6. El cliente no tiene más apuestas. Envia un batch de tamaño 0.
> 7. Servidor responde con una confirmacion, y se cierra la conexion.
> 8. El cliente se conecta al servidor.
> 9. El cliente envía solicitud de ganadores.
> 10.1. El servidor todavía no recibió todas las apuestas, le responde que el sorteo no fue finalizado. Cierra la conexion y vuelve al punto 6.
> 10.2. El servidor ya recibió todas las apuestas, verifica los ganadores y responde con la lista de ganadores para éste cliente (o 0 si ningun DNI de este cliente ganó). Cierra la conexion.
>
> En cuanto a las modificaciones que tuve que realizarle al servidor para acomodarse al nuevo protocolo, primero agregué en el loop printipal una funcion que se ocupa de recibir los 2 tipos de mensaje que puede recibir, y hacer algo al respecto.
> 
> En particular, si recibe un envio batch, se encarga de leer todas las apuestas y almacenarlas. 
> En el caso de que el batch sea te tamaño 0, agrega en un set de elementos, la agencia que ya terminó de enviar todos sus bets.
>
> En cambio, si recibe una solicitud de ganadores, verifica si ya se realizó el sorteo. Si no, responde que el sorteo no fue finalizado. Si ya se realizó, responde con la lista de ganadores para esa agencia.
>
> Para saber si el sorteo ya se realizó, en el loop principal, cada vez que algun cliente se desconecta, el servidor checkea si ya todas las agencias terminaron de enviar sus apuestas. Si es así, realiza el sorteo, y almacena los ganadores para cada agencia, y setea un flag indicando que el sorteo ya fue realizado.
>
>> Tuve un problema con la transmision de mensajes por el socket, que no lograba encontrar. Para resolverlo decidí utilizar wireshark, y poder ver el trafico de red real. Para poder ver mejor los paquetes enviados,implementé (con ayuda de LLM) un decodificador de paquetes personalizado en Lua para Wireshark. Esto me permitió filtrar y visualizar los mensajes específicos de mi protocolo, facilitando la identificación de problemas en la comunicación. Este decodificador es el que se encuentra en el archivo `custom.lua`



## Parte 3: Repaso de Concurrencia
En este ejercicio es importante considerar los mecanismos de sincronización a utilizar para el correcto funcionamiento de la persistencia.

### Ejercicio N°8:

Modificar el servidor para que permita aceptar conexiones y procesar mensajes en paralelo. En caso de que el alumno implemente el servidor en Python utilizando _multithreading_,  deberán tenerse en cuenta las [limitaciones propias del lenguaje](https://wiki.python.org/moin/GlobalInterpreterLock).

> #### Resolución:
> Una vez que en el servidor tenemos concurrencia para aceptar conexiones, ya no requerimos que los clientes se desconecten para permitir atender a nuevos clientes.
> Por eso, el protocolo nuevamente se modifica. En este caso, ya no se requiere que los clientes se desconecten una vez que han enviado todas sus apuestas. Simplemente pueden pedir inmediatamente el resultado del sorteo, aunque probablemente todavía no se encuentre disponible.
>
> Para implementar concurrencia con las conexiones, decidí utilizar multithreading. Si bien en python, la herramienta de multithreading no permite paralelismo real (a razon del GIL), como la tarea de responder las solicitudes de los clientes no es CPU intensiva, esto no representa un problema significativo.
>
> Para hacerlo, lo que hice fue mover toda la logica de comunicarme con un cliente a una clase separada: `ClientHandler`, que a su vez hereda de `threading.Thread`.
> Cuando se crea este cliente, se le asigna un socket y se inicia un nuevo hilo para manejar la comunicación con ese cliente.
> Todas las operaciones que puede hacer sin interferir con el estado general del servidor, las hace por si solas. Pero cada vez que necesita acceder a recursos compartidos, como almacenar las apuestas, debe llamar a una funcion de servidor, que se encarga de hacer el guardado de manera segura, utilizando Locks para prevenir que multiples hilos accedan a la misma informacion al mismo tiempo.

## Condiciones de Entrega
Se espera que los alumnos realicen un _fork_ del presente repositorio para el desarrollo de los ejercicios y que aprovechen el esqueleto provisto tanto (o tan poco) como consideren necesario.

Cada ejercicio deberá resolverse en una rama independiente con nombres siguiendo el formato `ej${Nro de ejercicio}`. Se permite agregar commits en cualquier órden, así como crear una rama a partir de otra, pero al momento de la entrega deberán existir 8 ramas llamadas: ej1, ej2, ..., ej7, ej8.
 (hint: verificar listado de ramas y últimos commits con `git ls-remote`)

Se espera que se redacte una sección del README en donde se indique cómo ejecutar cada ejercicio y se detallen los aspectos más importantes de la solución provista, como ser el protocolo de comunicación implementado (Parte 2) y los mecanismos de sincronización utilizados (Parte 3).

Se proveen [pruebas automáticas](https://github.com/7574-sistemas-distribuidos/tp0-tests) de caja negra. Se exige que la resolución de los ejercicios pase tales pruebas, o en su defecto que las discrepancias sean justificadas y discutidas con los docentes antes del día de la entrega. El incumplimiento de las pruebas es condición de desaprobación, pero su cumplimiento no es suficiente para la aprobación. Respetar las entradas de log planteadas en los ejercicios, pues son las que se chequean en cada uno de los tests.

La corrección personal tendrá en cuenta la calidad del código entregado y casos de error posibles, se manifiesten o no durante la ejecución del trabajo práctico. Se pide a los alumnos leer atentamente y **tener en cuenta** los criterios de corrección informados  [en el campus](https://campusgrado.fi.uba.ar/mod/page/view.php?id=73393).
