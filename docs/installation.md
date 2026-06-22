<!-- docs/installation.md -->
<h1>Instalación</h1>

<h2>Requisitos del Sistema</h2>
<ul>
    <li><strong>Python</strong> 3.8 o superior.</li>
    <li><strong>pip</strong> (gestor de paquetes de Python).</li>
</ul>

<h2>Dependencias</h2>
<p>El SDK depende de las siguientes bibliotecas (se instalan automáticamente):</p>
<ul>
    <li><code>requests</code> – Para peticiones HTTP.</li>
    <li><code>urllib3</code> – Cliente HTTP subyacente.</li>
    <li><code>pysocks</code> – Soporte para proxies SOCKS (opcional).</li>
</ul>

<h2>Instalación desde PyPI</h2>
<pre><code class="language-bash">pip install todus-sdk</code></pre>

<h2>Instalación desde el Código Fuente</h2>
<p>Clona el repositorio e instala en modo desarrollo:</p>
<pre><code class="language-bash">git clone https://github.com/tu-usuario/todus-sdk.git
cd todus-sdk
pip install -r requirements.txt</code></pre>

<h2>Verificar Instalación</h2>
<pre><code class="language-python">import todus
print(todus.__version__)  # Ejemplo: 1.5.2</code></pre>

<h2>Configuración de Proxy (Opcional)</h2>
<p>El SDK soporta proxies HTTP, SOCKS4 y SOCKS5 para entornos con restricciones de red.</p>
<pre><code class="language-python">from todus import ToDusClient2

# Ejemplo con SOCKS5
client = ToDusClient2(
    phone_number="5312345678",
    password="password",
    proxy="socks5://usuario:pass@proxy-server.com:1080"
)</code></pre>

<div class="admonition note">
    <p class="admonition-title">Nota sobre SSL</p>
    <p>Por defecto <code>verify_ssl=False</code> para compatibilidad. En producción, se recomienda establecer <code>verify_ssl=True</code> o instalar los certificados adecuados.</p>
</div>