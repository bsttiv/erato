<script setup lang="ts">
import Wordmark from '../components/atoms/Wordmark.vue'
import SiteFooter from '../components/organisms/SiteFooter.vue'
</script>

<template>
  <div class="min-h-screen bg-ground text-ink">
    <header class="page-x flex min-h-[76px] flex-wrap items-center justify-between gap-4 py-4">
      <Wordmark />
      <router-link to="/" class="btn-ghost btn-sm">Volver al inicio</router-link>
    </header>

    <main class="page-x py-12 sm:py-20">
      <div class="mx-auto max-w-[72ch]">
        <p class="text-sm text-brass">Información del servicio</p>
        <h1 class="mt-4 text-[44px] leading-tight sm:text-[60px]">Términos de servicio y Política de privacidad</h1>
        <p class="mt-6 text-base text-muted">Última actualización: 31 de octubre de 2026.</p>
        <nav class="mt-6 flex flex-wrap gap-x-6 gap-y-3" aria-label="Contenido legal">
          <a href="#terminos" class="underline underline-offset-4">Términos de servicio</a>
          <a href="#privacidad" class="underline underline-offset-4">Política de privacidad</a>
        </nav>

        <section id="terminos" class="scroll-mt-6 space-y-6 pt-12 text-base leading-relaxed" aria-labelledby="terms-title">
          <h2 id="terms-title" class="text-[36px] leading-tight">Términos de servicio</h2>
          <div>
            <h3 class="text-2xl">Qué ofrece Erato</h3>
            <p class="mt-2">Erato permite organizar composiciones personales o de una banda: letras, acordes, tablaturas, demos de audio y tareas. Los cambios se guardan explícitamente y se versionan por sección.</p>
          </div>
          <div>
            <h3 class="text-2xl">Cuenta y acceso</h3>
            <p class="mt-2">Para gestionar tus composiciones necesitas una cuenta. Protege tus credenciales y utiliza las opciones del perfil para revisar y cerrar tus sesiones. Una cuenta puede tener varias sesiones abiertas en distintos dispositivos.</p>
          </div>
          <div>
            <h3 class="text-2xl">Contenido y colaboración</h3>
            <p class="mt-2">Comparte únicamente contenido que tengas derecho a utilizar. Tú eliges la visibilidad de tus composiciones. Las composiciones personales privadas son accesibles para su dueño y las personas invitadas; las de una banda privada también son accesibles para sus integrantes. Una composición pública puede ser leída por cualquiera que tenga su enlace.</p>
            <p class="mt-3">Las invitaciones a composiciones distinguen entre lectores y editores. Los integrantes de una banda pueden editar sus composiciones. Publicar un enlace no concede permisos de edición.</p>
          </div>
          <div>
            <h3 class="text-2xl">Código abierto</h3>
            <p class="mt-2">El software de Erato se distribuye bajo la licencia AGPL-3.0. Puedes consultar el código y su licencia en <a href="https://github.com/bsttiv/erato" class="underline underline-offset-4">el repositorio de Erato</a>. La licencia del software no determina por sí sola la licencia de tus composiciones.</p>
          </div>
          <div>
            <h3 class="text-2xl">Responsable y contacto</h3>
            <p class="mt-2">Responsable del servicio: <strong>Bastián Valencia</strong>. Contacto para consultas sobre estos términos: <a href="mailto:bastian.valencia@ug.uchile.cl" class="underline underline-offset-4">bastian.valencia@ug.uchile.cl</a>.</p>
          </div>
        </section>

        <section id="privacidad" class="scroll-mt-6 space-y-6 pt-12 text-base leading-relaxed" aria-labelledby="privacy-title">
          <h2 id="privacy-title" class="text-[36px] leading-tight">Política de privacidad</h2>
          <div>
            <h3 class="text-2xl">Datos utilizados y finalidad</h3>
            <p class="mt-2">Erato utiliza tu correo electrónico, nombre de usuario, nombre visible y contraseña almacenada mediante hash para gestionar tu cuenta y el acceso. También guarda los datos de sesión, como el dispositivo y la fecha de acceso, para mantener y administrar tus sesiones.</p>
            <p class="mt-3">Las composiciones, las bandas, las invitaciones, las revisiones, los comentarios y las demos se utilizan para ofrecer las funciones de escritura, reproducción y colaboración. Solo el nombre visible y el nombre de usuario son datos públicos del perfil.</p>
          </div>
          <div>
            <h3 class="text-2xl">Sesiones y almacenamiento en el navegador</h3>
            <p class="mt-2">Las sesiones utilizan tokens de acceso y renovación. El navegador conserva una cookie de renovación no accesible desde JavaScript y un identificador de dispositivo en el almacenamiento local para el funcionamiento de la sesión. La gestión de sesiones se integra con Maestro, actualmente simulado mediante un mock.</p>
          </div>
          <div>
            <h3 class="text-2xl">Dónde se procesan los datos</h3>
            <p class="mt-2">Los datos de la aplicación se almacenan en MongoDB, con Atlas previsto para producción. Los archivos de audio se almacenan en Cloudinary. El alojamiento de la aplicación y del backend se realiza en Vercel. Estos servicios intervienen en el almacenamiento o procesamiento necesario para que Erato funcione.</p>
          </div>
          <div>
            <h3 class="text-2xl">Visibilidad del contenido</h3>
            <p class="mt-2">Los permisos de una composición determinan quién puede leerla y editarla. Si haces pública una composición, cualquier persona con su enlace podrá leer el contenido compartido. Revisa la visibilidad y las invitaciones antes de compartir información personal en letras, audios o comentarios.</p>
          </div>
          <div>
            <h3 class="text-2xl">Conservación de datos</h3>
            <ul class="mt-2 list-disc space-y-2 pl-5">
              <li>Tu cuenta y tu perfil se conservan mientras la cuenta exista. La aplicación todavía no permite eliminar la cuenta directamente: se elimina a petición, con el procedimiento de la sección siguiente.</li>
              <li>Tus composiciones se conservan hasta que las borres. Al borrar una composición se eliminan también sus demos, comentarios, revisiones, invitaciones y accesos.</li>
              <li>De cada sección de una composición se guardan las últimas 50 revisiones; las anteriores se eliminan automáticamente.</li>
              <li>Una sesión vence a los 7 días si no se renueva, y puedes cerrarla antes desde tu perfil. Los registros de intentos de inicio de sesión se eliminan a los 15 minutos.</li>
              <li>Los datos borrados pueden permanecer en las copias de seguridad de los proveedores hasta que estas caduquen según su configuración.</li>
            </ul>
          </div>
          <div>
            <h3 class="text-2xl">Solicitudes sobre tus datos</h3>
            <p class="mt-2">Puedes modificar los datos que permite el perfil, administrar tus sesiones y editar o borrar composiciones según tus permisos. Para pedir acceso, corrección, copia o eliminación de tus datos, o la eliminación de tu cuenta, escribe a <a href="mailto:bastian.valencia@ug.uchile.cl" class="underline underline-offset-4">bastian.valencia@ug.uchile.cl</a> desde el correo de tu cuenta e indica tu nombre de usuario y qué necesitas.</p>
            <p class="mt-3">Si no se puede confirmar que la cuenta es tuya, se te pedirá la información mínima para verificarlo. Recibirás una respuesta en un plazo máximo de 30 días corridos desde que se confirme tu identidad.</p>
          </div>
        </section>
      </div>
    </main>

    <SiteFooter />
  </div>
</template>
