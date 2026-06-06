# Manual Profesional y Didactico de Instalacion de Arch Linux + KDE Plasma en Dual Boot con Windows

Version: 1.0 (Borrador tecnico para convertir a PDF)
Fecha: 2026-06-06
Nivel: Desde principiante guiado hasta instalacion manual avanzada
Objetivo: proceso detallado, verificable y con mitigacion de errores para instalar Arch Linux junto a Windows.

---

## Indice General

1. [Proposito del documento](#1-proposito-del-documento)
2. [Perfil del lector y alcance](#2-perfil-del-lector-y-alcance)
3. [Advertencias criticas y politica de seguridad](#3-advertencias-criticas-y-politica-de-seguridad)
4. [Arquitectura objetivo del sistema](#4-arquitectura-objetivo-del-sistema)
5. [Glosario tecnico rapido](#5-glosario-tecnico-rapido)
6. [Checklist maestro previo](#6-checklist-maestro-previo)
7. [Fase A - Preparacion en Windows](#7-fase-a---preparacion-en-windows)
8. [Fase B - Preparacion de firmware UEFI/BIOS](#8-fase-b---preparacion-de-firmware-uefibios)
9. [Fase C - Arranque de la ISO y validaciones iniciales](#9-fase-c---arranque-de-la-iso-y-validaciones-iniciales)
10. [Ruta 1: Instalacion con archinstall](#10-ruta-1-instalacion-con-archinstall)
11. [Ruta 2: Instalacion manual completa](#11-ruta-2-instalacion-manual-completa)
12. [Post-instalacion obligatoria (comun para ambas rutas)](#12-post-instalacion-obligatoria-comun-para-ambas-rutas)
13. [Hardening y buenas practicas de estabilidad](#13-hardening-y-buenas-practicas-de-estabilidad)
14. [Validacion final de dual boot y entorno KDE](#14-validacion-final-de-dual-boot-y-entorno-kde)
15. [Troubleshooting profundo por escenarios](#15-troubleshooting-profundo-por-escenarios)
16. [Mantenimiento operativo (runbook)](#16-mantenimiento-operativo-runbook)
17. [Anexo A - Scripts de apoyo opcionales](#17-anexo-a---scripts-de-apoyo-opcionales)
18. [Anexo B - Plantilla para convertir a PDF](#18-anexo-b---plantilla-para-convertir-a-pdf)
19. [Anexo C - FAQ de decisiones de diseno](#19-anexo-c---faq-de-decisiones-de-diseno)

---

## 1) Proposito del documento

Este README esta diseñado para ser un manual profesional y ultra didactico, con enfoque "a prueba de fallas" dentro de lo razonable. No solo lista comandos: tambien explica para que sirve cada bloque, como verificar el resultado esperado y que hacer si algo no coincide.

Objetivos principales:

- Instalar Arch Linux en dual boot con Windows sin perder informacion del sistema existente.
- Entregar dos caminos completos:
  - Ruta 1: `archinstall` (guiada y mas rapida).
  - Ruta 2: instalacion manual (control absoluto y aprendizaje real de Arch).
- Instalar KDE Plasma con configuracion moderna de red, audio y servicios base.
- Dejar un sistema estable, actualizable y listo para uso diario.

---

## 2) Perfil del lector y alcance

Este manual asume que:

- Tu equipo ya tiene Windows funcional.
- Quieres dual boot real, no maquina virtual.
- Estaras en modo UEFI y tabla de particiones GPT.
- Sabes seguir comandos con disciplina (copiar/pegar con validacion, no a ciegas).

Fuera de alcance en esta version:

- Cifrado completo con LUKS (se menciona orientativamente).
- RAID complejo.
- Servidores sin entorno grafico.

---

## 3) Advertencias criticas y politica de seguridad

Regla de oro:

- Nunca ejecutes comandos de particionado sin verificar dos veces el disco objetivo.

Riesgos principales:

1. Seleccionar disco equivocado y borrar Windows o datos.
2. Montar mal la particion EFI y romper el arranque.
3. Omitir `fstab` correcto y que el sistema no bootee.
4. Olvidar habilitar red o display manager y entrar en bucle de consola.

Politica de seguridad operativa:

- Antes de cada paso destructivo: identificar, confirmar, ejecutar, validar.
- Si un comando da error: detenerse, no encadenar comandos ciegamente.
- Mantener un registro manual de tus nombres reales de particiones.

---

## 4) Arquitectura objetivo del sistema

Resultado esperado:

- Windows permanece funcional.
- Arch Linux instalado en particiones separadas.
- Boot manager con entrada para ambos sistemas.
- KDE Plasma funcional con login grafico (SDDM).
- Red y audio operativos.

Topologia recomendada para dual boot (ejemplo):

- Disco: `/dev/nvme0n1`
- Particion EFI existente (Windows): `/dev/nvme0n1p1` (FAT32)
- Nueva particion root Arch: `/dev/nvme0n1p5` (ext4)
- Nueva swap Arch: `/dev/nvme0n1p6`
- Nueva home Arch: `/dev/nvme0n1p7` (ext4)

Nota: tus nombres reales pueden ser distintos (`/dev/sda`, `p2`, etc.).

---

## 5) Glosario tecnico rapido

- UEFI: firmware moderno de arranque.
- GPT: esquema de particiones recomendado para UEFI.
- ESP/EFI: particion FAT32 de arranque UEFI.
- `chroot`: entrar al sistema instalado desde el live ISO.
- `GRUB`: gestor de arranque multiboot.
- `os-prober`: detecta otros sistemas (Windows) para GRUB.
- `NetworkManager`: administracion de red.
- `PipeWire`: stack moderno de audio/video.

---

## 6) Checklist maestro previo

Marca todo antes de iniciar:

- [ ] Backup de archivos criticos (nube y/o disco externo).
- [ ] Clave de recuperacion BitLocker guardada.
- [ ] ISO oficial de Arch descargada.
- [ ] USB booteable creada correctamente (UEFI/GPT).
- [ ] Espacio no asignado en disco para Arch.
- [ ] Confirmado arranque Windows en modo UEFI.
- [ ] Tiempo disponible sin interrupciones.

Si alguno esta en no, no empieces aun.

---

## 7) Fase A - Preparacion en Windows

### A.1 Reducir particion de Windows

1. Abre Administracion de discos:
   - `Win + X` -> Administracion de discos.
2. Clic derecho sobre C: -> Reducir volumen.
3. Liberar espacio recomendado:
   - Minimo funcional: 40 GB.
   - Recomendado para uso comodo: 80-150 GB.
4. Deja el espacio como "No asignado".

Validacion:

- Debes ver una region "No asignado" en negro.
- No crear volumen nuevo en Windows.

### A.2 Confirmar UEFI

1. `Win + R` -> `msinfo32`.
2. Revisar "Modo de BIOS": debe indicar `UEFI`.

### A.3 Preparar Fast Startup y BitLocker

Recomendado para evitar conflictos de montaje NTFS:

- Desactivar inicio rapido de Windows (Power Options).
- Suspender o desactivar BitLocker durante instalacion.

### A.4 Crear USB booteable

Opciones:

- Rufus (modo GPT + UEFI).
- Ventoy.

Validacion:

- La BIOS detecta la USB como entrada UEFI.

---

## 8) Fase B - Preparacion de firmware UEFI/BIOS

Entrar a BIOS/UEFI y revisar:

- Secure Boot: Off (temporal para simplificar).
- Fast Boot: Off (temporal).
- Boot mode: UEFI (no Legacy/CSM).
- Orden de arranque: USB primero.

Nota formal:

- Luego de un sistema estable puedes re-evaluar Secure Boot con configuracion avanzada.

---

## 9) Fase C - Arranque de la ISO y validaciones iniciales

Arranca desde USB en entrada UEFI.

Comandos iniciales:

```bash
ls /sys/firmware/efi/efivars
```

Que valida:

- Si lista contenido, estas en UEFI.
- Si falla, arrancaste en modo incorrecto.

Red:

```bash
ip a
ping -c 3 archlinux.org
```

Que valida:

- Interfaz activa y salida a internet.

Sincronizacion horaria:

```bash
timedatectl set-ntp true
timedatectl status
```

Que valida:

- Hora adecuada para evitar problemas de llaves/paquetes.

Validacion de discos antes de tocar particiones:

```bash
lsblk -o NAME,SIZE,FSTYPE,TYPE,MOUNTPOINT
fdisk -l
```

---

## 10) Ruta 1: Instalacion con archinstall

Esta ruta es ideal si quieres reducir complejidad inicial sin perder control esencial.

### 10.1 Lanzar asistente

```bash
archinstall
```

### 10.2 Configuracion recomendada (dual boot conservador)

1. Mirrors/Region

- Elige mirrors cercanos para velocidad.

2. Locale y teclado

- `es_ES.UTF-8` o el locale que prefieras.
- Keymap segun tu teclado.

3. Disk configuration

- Usa modo de particionado manual dentro del instalador.
- Selecciona solo espacio libre.
- Reusa particion EFI existente de Windows (no formatear).

4. Filesystem

- Recomendado para estabilidad inicial: `ext4`.

5. Swap

- 2-8 GB segun RAM y necesidad de hibernacion.

6. Bootloader

- Recomendado: `GRUB` para dual boot mas predecible.

7. Perfil de escritorio

- Desktop: KDE Plasma.

8. Audio

- PipeWire.

9. Red

- `NetworkManager` activado.

10. Cuentas

- Define root password.
- Crea usuario normal (imprescindible).

11. Paquetes adicionales sugeridos

- `base-devel git nano vim wget curl os-prober ntfs-3g`

### 10.3 Punto de control antes de confirmar

Validar que:

- No aparezca accion de borrado completo del disco Windows.
- EFI seleccionada sea la existente.
- Particiones Linux esten en el espacio no asignado.

### 10.4 Instalar y reiniciar

Tras finalizar:

```bash
reboot
```

Retira USB al reiniciar.

### 10.5 Si archinstall no detecta bien dual boot

Plan de contingencia:

- Completa instalacion.
- Entra a Arch y aplica seccion de GRUB del capitulo 12/15 para detectar Windows.

---

## 11) Ruta 2: Instalacion manual completa

Esta ruta es la mas didactica y profesional para entender Arch de verdad.

### 11.0 Mapa de trabajo

1. Identificar dispositivos.
2. Crear particiones Linux nuevas.
3. Formatear particiones Linux.
4. Montar raiz/home/efi.
5. Instalar base con `pacstrap`.
6. Generar `fstab`.
7. Entrar con `arch-chroot`.
8. Configurar sistema, usuarios, red, bootloader.
9. Instalar KDE y habilitar servicios.
10. Reiniciar y validar.

### 11.1 Identificar discos y particiones

```bash
lsblk -o NAME,SIZE,FSTYPE,TYPE,MOUNTPOINT
fdisk -l
```

Como leer salida:

- Busca disco principal (`nvme0n1` o `sda`).
- Identifica EFI de Windows (FAT32, pequena, tipo EFI System).
- Ubica espacio libre para nuevas particiones Linux.

Punto de control obligatorio:

- Anota en papel o bloc:
  - Disco objetivo.
  - EFI Windows.
  - IDs de nuevas particiones Linux.

### 11.2 Crear particiones Linux

Herramienta amigable en consola:

```bash
cfdisk /dev/nvme0n1
```

Ejemplo de diseno:

- Root (`/`): 60G
- Swap: 8G
- Home (`/home`): resto

Tipos:

- Root/Home: Linux filesystem
- Swap: Linux swap

Regla critica:

- No tocar particiones de Windows.
- No borrar EFI de Windows.

### 11.3 Formatear particiones Linux

Ejemplo (ajusta segun tu caso real):

```bash
mkfs.ext4 /dev/nvme0n1p5
mkswap /dev/nvme0n1p6
mkfs.ext4 /dev/nvme0n1p7
swapon /dev/nvme0n1p6
```

Explicacion:

- `mkfs.ext4 ...p5`: crea filesystem root.
- `mkswap ...p6`: inicializa swap.
- `mkfs.ext4 ...p7`: crea filesystem home.
- `swapon ...p6`: activa swap en entorno live.

Validacion:

```bash
lsblk -f
swapon --show
```

### 11.4 Montar estructura del nuevo sistema

```bash
mount /dev/nvme0n1p5 /mnt
mkdir -p /mnt/home
mount /dev/nvme0n1p7 /mnt/home
mkdir -p /mnt/boot/efi
mount /dev/nvme0n1p1 /mnt/boot/efi
```

Explicacion:

- `/mnt` sera la raiz del sistema futuro.
- `/mnt/boot/efi` debe montar la EFI ya existente.

Validacion:

```bash
findmnt /mnt
```

Debe mostrar root, home y efi correctamente montados.

### 11.5 Instalar base del sistema

```bash
pacstrap -K /mnt base linux linux-firmware networkmanager sudo nano vim grub efibootmgr os-prober base-devel
```

Explicacion:

- `base`, `linux`, `linux-firmware`: nucleo y base del SO.
- `networkmanager`: red.
- `sudo`: privilegios controlados.
- `grub`, `efibootmgr`, `os-prober`: arranque dual boot.

### 11.6 Generar fstab robusto

```bash
genfstab -U /mnt >> /mnt/etc/fstab
cat /mnt/etc/fstab
```

Validacion obligatoria:

- Deben aparecer UUID para `/`, `/home`, `/boot/efi` y swap.
- Si falta alguna linea, corrige antes de continuar.

### 11.7 Entrar al sistema instalado

```bash
arch-chroot /mnt
```

A partir de aqui ya trabajas dentro del Arch instalado.

### 11.8 Configuracion regional y reloj

Zona horaria (ejemplo America/Lima):

```bash
ln -sf /usr/share/zoneinfo/America/Lima /etc/localtime
hwclock --systohc
```

Locales:

```bash
nano /etc/locale.gen
```

Descomenta, por ejemplo:

- `en_US.UTF-8 UTF-8`
- `es_ES.UTF-8 UTF-8`

Genera y define locale:

```bash
locale-gen
echo "LANG=es_ES.UTF-8" > /etc/locale.conf
```

Teclado de consola (opcional):

```bash
echo "KEYMAP=la-latin1" > /etc/vconsole.conf
```

### 11.9 Hostname y hosts

```bash
echo "archkde" > /etc/hostname
cat > /etc/hosts << 'EOF'
127.0.0.1 localhost
::1       localhost
127.0.1.1 archkde.localdomain archkde
EOF
```

### 11.10 Password root y usuario operativo

Root:

```bash
passwd
```

Usuario normal:

```bash
useradd -m -G wheel -s /bin/bash tuusuario
passwd tuusuario
```

Habilitar sudo para wheel:

```bash
EDITOR=nano visudo
```

Descomentar linea:

```text
%wheel ALL=(ALL:ALL) ALL
```

### 11.11 Red al arranque

```bash
systemctl enable NetworkManager
```

### 11.12 Bootloader GRUB para dual boot

Instalar en UEFI:

```bash
grub-install --target=x86_64-efi --efi-directory=/boot/efi --bootloader-id=ArchLinux
```

Habilitar deteccion de Windows:

```bash
sed -i 's/^#GRUB_DISABLE_OS_PROBER=false/GRUB_DISABLE_OS_PROBER=false/' /etc/default/grub
```

Si no existe la linea:

```bash
echo 'GRUB_DISABLE_OS_PROBER=false' >> /etc/default/grub
```

Generar configuracion:

```bash
grub-mkconfig -o /boot/grub/grub.cfg
```

Validacion critica:

- En la salida de `grub-mkconfig` deberias ver algo como "Found Windows Boot Manager".

### 11.13 Instalar KDE Plasma + SDDM + audio

```bash
pacman -S --needed xorg plasma kde-applications sddm pipewire pipewire-alsa pipewire-pulse wireplumber
systemctl enable sddm
```

Explicacion:

- `xorg`: base grafica.
- `plasma`: escritorio KDE.
- `kde-applications`: suite de utilidades.
- `sddm`: login grafico.
- PipeWire stack: audio moderno.

### 11.14 Salida limpia y reinicio

```bash
exit
umount -R /mnt
swapoff -a
reboot
```

Retira USB.

---

## 12) Post-instalacion obligatoria (comun para ambas rutas)

Al entrar a Arch por primera vez:

### 12.1 Actualizacion base

```bash
sudo pacman -Syu
```

### 12.2 Paquetes de operacion diaria

```bash
sudo pacman -S --needed git curl wget unzip zip htop neofetch ntfs-3g ufw firefox
```

### 12.3 Servicios recomendados

```bash
sudo systemctl enable --now NetworkManager
sudo systemctl enable --now sddm
```

Bluetooth e impresion (opcional):

```bash
sudo pacman -S --needed bluez bluez-utils cups
sudo systemctl enable --now bluetooth
sudo systemctl enable --now cups
```

### 12.4 Firewall base

```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw enable
sudo ufw status verbose
```

### 12.5 Verificacion funcional rapida

- [ ] Inicia sesion en KDE.
- [ ] Tienes internet.
- [ ] Audio funciona.
- [ ] En reinicio aparece menu de GRUB con Windows.

---

## 13) Hardening y buenas practicas de estabilidad

### 13.1 Reglas de oro para no romper Arch

- Actualiza de forma completa (`pacman -Syu`), no parcial.
- Lee noticias de Arch antes de upgrades grandes.
- Evita mezclar repos no confiables al inicio.

### 13.2 Snapshot/backup recomendado

Si mas adelante migras a Btrfs, habilita snapshots.
Para ext4, usa backups periodicos con `rsync`.

Ejemplo backup de home a disco externo:

```bash
rsync -aAXHv --delete /home/tuusuario/ /run/media/tuusuario/TU_DISCO/backup-home/
```

### 13.3 Logs y diagnostico

Comandos clave:

```bash
journalctl -b -p err
systemctl --failed
```

---

## 14) Validacion final de dual boot y entorno KDE

Checklist de entrega (estado "pro"):

- [ ] GRUB muestra Arch y Windows.
- [ ] Arch inicia en modo grafico KDE sin errores.
- [ ] Windows inicia normal desde GRUB.
- [ ] Red operativa por cable y/o wifi.
- [ ] Audio funcional en KDE.
- [ ] `sudo` funciona en usuario normal.
- [ ] Sistema actualizado sin paquetes rotos.

Validaciones por comando:

```bash
cat /etc/fstab
lsblk -f
sudo efibootmgr -v
systemctl status sddm NetworkManager --no-pager
```

---

## 15) Troubleshooting profundo por escenarios

### Escenario 1: No aparece Windows en GRUB

1. Verifica `os-prober`:

```bash
sudo pacman -S os-prober
```

2. Verifica configuracion:

```bash
grep GRUB_DISABLE_OS_PROBER /etc/default/grub
```

Debe estar en `false`.

3. Regenera GRUB:

```bash
sudo grub-mkconfig -o /boot/grub/grub.cfg
```

4. Si sigue sin salir, comprueba particion EFI de Windows:

```bash
sudo ls /boot/efi/EFI
```

Debes ver carpeta de Microsoft.

### Escenario 2: Arranca a consola, no a KDE

```bash
sudo systemctl status sddm
sudo systemctl enable --now sddm
```

Si falta KDE:

```bash
sudo pacman -S plasma sddm xorg
```

### Escenario 3: Sin internet tras reinicio

```bash
sudo systemctl status NetworkManager
sudo systemctl enable --now NetworkManager
nmcli device status
```

### Escenario 4: Error de montaje en boot

1. Bootea ISO.
2. Monta sistema y revisa `fstab`:

```bash
mount /dev/nvme0n1p5 /mnt
cat /mnt/etc/fstab
lsblk -f
```

3. Corrige UUID incorrectos.

### Escenario 5: Hora desfasada entre Windows y Arch

Opcion menos ideal pero practica en dual boot:

```bash
timedatectl set-local-rtc 1 --adjust-system-clock
```

### Escenario 6: GRUB da error en una reparacion

Desde ISO:

```bash
mount /dev/nvme0n1p5 /mnt
mount /dev/nvme0n1p1 /mnt/boot/efi
arch-chroot /mnt
grub-install --target=x86_64-efi --efi-directory=/boot/efi --bootloader-id=ArchLinux
grub-mkconfig -o /boot/grub/grub.cfg
exit
umount -R /mnt
reboot
```

---

## 16) Mantenimiento operativo (runbook)

### 16.1 Actualizacion segura

```bash
sudo pacman -Syu
```

### 16.2 Buscar paquetes

```bash
pacman -Ss termino
```

### 16.3 Limpiar cache de paquetes

```bash
sudo paccache -rk3
```

### 16.4 Ver consumo de disco

```bash
df -h
sudo du -xh / | sort -h | tail -n 40
```

### 16.5 Revisar fallos de arranque actual

```bash
journalctl -b -p warning
```

### 16.6 Regla de updates pro

Antes de actualizar:

```bash
ping -c 2 archlinux.org
sudo pacman -Syy
sudo pacman -Syu
```

Despues de actualizar:

```bash
systemctl --failed
journalctl -b -p err --no-pager
```

---

## 17) Anexo A - Scripts de apoyo opcionales

Importante:

- Son scripts de apoyo para acelerar validaciones.
- No sustituyen entender los pasos.
- Ajusta nombres de particiones antes de ejecutar.

### A) Script de pre-chequeo en live ISO

Guardar como `precheck-live.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

echo "[1/6] Verificando UEFI..."
if [ -d /sys/firmware/efi/efivars ]; then
  echo "OK: Sistema en modo UEFI"
else
  echo "ERROR: No estas en UEFI"
  exit 1
fi

echo "[2/6] Verificando red..."
if ping -c 1 archlinux.org >/dev/null 2>&1; then
  echo "OK: Internet funcional"
else
  echo "ERROR: Sin internet"
  exit 1
fi

echo "[3/6] Listando discos..."
lsblk -o NAME,SIZE,FSTYPE,TYPE,MOUNTPOINT

echo "[4/6] Hora NTP..."
timedatectl set-ntp true

echo "[5/6] Estado de tiempo..."
timedatectl status | sed -n '1,8p'

echo "[6/6] Progreso listo para instalacion."
```

Uso:

```bash
chmod +x precheck-live.sh
./precheck-live.sh
```

### B) Script de post-chequeo en sistema instalado

Guardar como `postcheck-arch.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

echo "== Estado de servicios clave =="
systemctl is-enabled NetworkManager || true
systemctl is-enabled sddm || true

echo "== Estado red =="
nmcli device status || true

echo "== fstab =="
cat /etc/fstab

echo "== Boot entries =="
efibootmgr -v || true

echo "== Kernel y sistema =="
uname -a
cat /etc/os-release

echo "Post-check completado."
```

Uso:

```bash
chmod +x postcheck-arch.sh
./postcheck-arch.sh
```

### C) Script de reparacion guiada de GRUB (para usar con cuidado)

Guardar como `repair-grub.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

ROOT_PART="${1:-}"
EFI_PART="${2:-}"

if [ -z "$ROOT_PART" ] || [ -z "$EFI_PART" ]; then
  echo "Uso: ./repair-grub.sh /dev/nvme0n1p5 /dev/nvme0n1p1"
  exit 1
fi

mount "$ROOT_PART" /mnt
mkdir -p /mnt/boot/efi
mount "$EFI_PART" /mnt/boot/efi

arch-chroot /mnt bash -c '
  grub-install --target=x86_64-efi --efi-directory=/boot/efi --bootloader-id=ArchLinux
  sed -i "s/^#GRUB_DISABLE_OS_PROBER=false/GRUB_DISABLE_OS_PROBER=false/" /etc/default/grub || true
  grep -q "^GRUB_DISABLE_OS_PROBER=false" /etc/default/grub || echo "GRUB_DISABLE_OS_PROBER=false" >> /etc/default/grub
  grub-mkconfig -o /boot/grub/grub.cfg
'

echo "Reparacion GRUB completada."
```

Uso:

```bash
chmod +x repair-grub.sh
./repair-grub.sh /dev/nvme0n1p5 /dev/nvme0n1p1
```

---

## 18) Anexo B - Plantilla para convertir a PDF

Estructura sugerida para version formal final:

1. Portada:
   - Titulo.
   - Autor.
   - Fecha.
   - Version.
2. Resumen ejecutivo.
3. Requisitos y riesgos.
4. Procedimiento Ruta 1 (`archinstall`).
5. Procedimiento Ruta 2 (manual).
6. Validaciones y pruebas.
7. Troubleshooting.
8. Conclusiones.
9. Anexos de scripts y comandos.

Sugerencia para enriquecer al exportar PDF:

- Agregar capturas por hito:
  - Administracion de discos en Windows.
  - Pantallas de `archinstall`.
  - Salida de `lsblk -f`.
  - Salida de `grub-mkconfig` detectando Windows.
  - Escritorio KDE inicial.

---

## 19) Anexo C - FAQ de decisiones de diseno

### C.1 Por que GRUB y no systemd-boot en este manual

Porque en dual boot con Windows, GRUB suele ser mas flexible en deteccion y recuperacion inicial para usuarios nuevos.

### C.2 Por que ext4 en lugar de Btrfs para empezar

Porque ext4 reduce complejidad inicial y facilita aprendizaje base de Arch. Btrfs puede ser segunda iteracion.

### C.3 Que cambia si tengo AMD o Intel

Poco en el flujo principal. Solo conviene instalar microcode:

Intel:

```bash
sudo pacman -S intel-ucode
```

AMD:

```bash
sudo pacman -S amd-ucode
```

Luego regenerar GRUB:

```bash
sudo grub-mkconfig -o /boot/grub/grub.cfg
```

### C.4 Puedo usar este manual en laptop con un solo disco

Si. Es justo el caso principal. Solo respeta la regla de no tocar particiones de Windows fuera del espacio no asignado.

### C.5 Cuanto espacio real necesito para ir comodo

- Minimo funcional: 40 GB.
- Comodo para trabajo diario: 80-150 GB.
- Desarrollo + multimedia/juegos: 150+ GB.

---

## Cierre

Si sigues este manual con disciplina de validacion paso a paso, obtendras una instalacion profesional de Arch Linux + KDE Plasma en dual boot con Windows, minimizando errores comunes de particionado, EFI y arranque.

Para una siguiente iteracion se puede agregar:

- Edicion con cifrado LUKS.
- Edicion con Btrfs + snapshots.
- Edicion con Secure Boot correctamente firmado.
