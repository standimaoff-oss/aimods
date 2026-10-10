# NOTICE — сторонний код и атрибуция

## Volumetric Pyro (volpyro 1.5.6), MIT

Часть шейдера дыма `mods/aiarsenal/src/main/resources/assets/aiarsenal/shaders/core/volsmoke.fsh` (r28) —
освещение и эмиссия — перенесена из мода **Volumetric Pyro: Smoke, Explosions & Rocket Plumes**
версии 1.5.6 (`volpyro-1.5.6-nuclear (1).jar`, файл в корне репозитория на ветке `main`).

- Метаданные мода: `license = "MIT"`, `authors = "VolPyro Contributors"`.
- Перенесено: dual-lobe Henyey-Greenstein фаза, multiple-scattering сумма, billow-октавы плотности,
  blackbody-эмиссия. Формулы адаптированы под наш интерфейс (сферы-пуфы вместо полноэкранного raymarch).
- Упоминание в заголовке шейдера ссылается на этот файл.

Текст лицензии MIT, которым распространяется этот код:

```
MIT License

Copyright (c) VolPyro Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

Примечание: в самом jar файла с текстом лицензии нет (только `mods.toml`), поэтому стандартный текст MIT
приведён выше по метаданным мода. Точного года и полного списка держателей авторских прав в метаданных нет.
