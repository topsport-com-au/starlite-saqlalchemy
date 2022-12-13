# Changelog

<!--next-version-placeholder-->

## v0.17.0 (2022-12-13)
### Feature
* Follow starlite into msgspec. ([#165](https://github.com/topsport-com-au/starlite-saqlalchemy/issues/165)) ([`2104626`](https://github.com/topsport-com-au/starlite-saqlalchemy/commit/2104626ff9016ba97675c0489d62f5106f1a9757))

### Breaking
* follow starlite into msgspec. ([#165](https://github.com/topsport-com-au/starlite-saqlalchemy/issues/165)) ([`2104626`](https://github.com/topsport-com-au/starlite-saqlalchemy/commit/2104626ff9016ba97675c0489d62f5106f1a9757))

## v0.16.0 (2022-12-08)
### Feature
* **repo:** Abstract method `filter_collection_by_kwargs()` ([#159](https://github.com/topsport-com-au/starlite-saqlalchemy/issues/159)) ([`15bf7a8`](https://github.com/topsport-com-au/starlite-saqlalchemy/commit/15bf7a814da21e105fc26b98a876f68fa0c998b4))

## v0.15.0 (2022-12-05)
### Feature
* **testing:** ControllerTest utility. ([#152](https://github.com/topsport-com-au/starlite-saqlalchemy/issues/152)) ([`4cc707b`](https://github.com/topsport-com-au/starlite-saqlalchemy/commit/4cc707bf25b4493b0477df173040f0fa4454fe1c))

## v0.14.2 (2022-12-03)
### Fix
* **dto:** Fix UnionType parsing as relationship. ([`4b93d17`](https://github.com/topsport-com-au/starlite-saqlalchemy/commit/4b93d17e732849179bb1c2d014d8177a93a3dbfc))

## v0.14.1 (2022-11-30)
### Fix
* Fix for usage of mock repo. ([`dddf1e2`](https://github.com/topsport-com-au/starlite-saqlalchemy/commit/dddf1e2e52defbb7632368c8442417fa26076e74))

### Documentation
* **changelog:** Add missing entry ([`e88a510`](https://github.com/topsport-com-au/starlite-saqlalchemy/commit/e88a5103c7107707a864a99e7eeef25a8a68daa8))

## v0.14.0 (2022-11-28)
### Breaking
* Overhaul of DTO pattern ([`e503447`](https://github.com/topsport-com-au/starlite-saqlalchemy/commit/e5034479b028ef791a4947b5df5a14cf248e935c))

## v0.13.1 (2022-11-24)
### Fix
* **testing:** Fix GenericMockRepository collections. ([#136](https://github.com/topsport-com-au/starlite-saqlalchemy/issues/136)) ([`246c103`](https://github.com/topsport-com-au/starlite-saqlalchemy/commit/246c10305c8436f47142cd6208ba4bcf85017f17))

## v0.13.0 (2022-11-21)
### Feature
* Simplify service and repo. ([#134](https://github.com/topsport-com-au/starlite-saqlalchemy/issues/134)) ([`ed3b59a`](https://github.com/topsport-com-au/starlite-saqlalchemy/commit/ed3b59aea64d82bdc75ef4fca65b93b6fcf45d4c))

### Breaking
* simplify service and repo. ([#134](https://github.com/topsport-com-au/starlite-saqlalchemy/issues/134)) ([`ed3b59a`](https://github.com/topsport-com-au/starlite-saqlalchemy/commit/ed3b59aea64d82bdc75ef4fca65b93b6fcf45d4c))

## v0.12.1 (2022-11-21)
### Fix
* **log:** Exclude compressed body from log output. ([`4d47df5`](https://github.com/topsport-com-au/starlite-saqlalchemy/commit/4d47df59a7a2b4968921a5204a912be045075a93))

### Documentation
* **readme:** Add coverage badge. ([`3c44375`](https://github.com/topsport-com-au/starlite-saqlalchemy/commit/3c44375c81f94cf8214906af25312f1d52547fd0))

## v0.12.0 (2022-11-17)
### Feature
* **worker:** Set queue name so saq keys unique to application ([`c56a12f`](https://github.com/topsport-com-au/starlite-saqlalchemy/commit/c56a12f9390c2f8185fa5831115cca79d65e3120))

## v0.11.0 (2022-11-17)
### Feature
* **dto:** Relationship support + test for forward refs ([`1bb3fb3`](https://github.com/topsport-com-au/starlite-saqlalchemy/commit/1bb3fb3ceaddfb440531d582ea1b852792983629))
* **logging:** Configurable dependency log levels. ([`a4fda6d`](https://github.com/topsport-com-au/starlite-saqlalchemy/commit/a4fda6dc5de64c8e4ca45ac42d96fa808677439d))

## v0.10.0 (2022-11-17)
### Feature
* **service:** __class_getitem__ sets `repository_type` on service. ([`4127f3a`](https://github.com/topsport-com-au/starlite-saqlalchemy/commit/4127f3aec85560b1f17eaf90518f94d83e0ef5fd))
* **repository:** __class_getitem__ sets `model_type` on repo. ([`d81e6c6`](https://github.com/topsport-com-au/starlite-saqlalchemy/commit/d81e6c6df972c5d8d919e8d9c398404b57acfd8f))

## v0.9.0 (2022-11-17)
### Feature
* **logging:** Improve dev logging experience ([`fc04a99`](https://github.com/topsport-com-au/starlite-saqlalchemy/commit/fc04a9914d8210e9729bfc3857bc555d4ccfa1d1))
* **plugin:** Set starlite debug ([`1a9e01d`](https://github.com/topsport-com-au/starlite-saqlalchemy/commit/1a9e01d6e5a9b91e81c417e7af4bb5ce98dc586e))

### Fix
* **logging:** Don't log exceptions that are http and < 500 status ([`6b42e48`](https://github.com/topsport-com-au/starlite-saqlalchemy/commit/6b42e48053b09828ee220f0b6b6fc5f991e4536a))
* **logging:** Don't log exceptions that are http and < 500 status ([`bce531d`](https://github.com/topsport-com-au/starlite-saqlalchemy/commit/bce531d6431c8d0b5f3cb74bf57367d25c078721))

## v0.8.1 (2022-11-16)
### Fix
* **scripts:** Set `factory` setting on uvicorn config. ([`bce93f3`](https://github.com/topsport-com-au/starlite-saqlalchemy/commit/bce93f3817c6c8647fc3dc5521eb12b04f77bdad))

## v0.8.0 (2022-11-16)
### Feature
* **app:** Support for using app factory. ([`a176908`](https://github.com/topsport-com-au/starlite-saqlalchemy/commit/a1769085a61f09cf4991448313a6164f488adf79))

## v0.7.2 (2022-11-14)
### Fix
* **saq:** Upgrade to typed release. ([`7ac37c3`](https://github.com/topsport-com-au/starlite-saqlalchemy/commit/7ac37c3ac6eddbd2b51e7e3a9b2512889eeddb53))

## v0.7.1 (2022-11-14)
### Fix
* **run_app:** Fix run app script. ([`db1ecca`](https://github.com/topsport-com-au/starlite-saqlalchemy/commit/db1ecca96f472716bedc3c35089bd71948a95c22))

## v0.7.0 (2022-11-14)
### Feature
* **app:** Startup script. ([`1781c7a`](https://github.com/topsport-com-au/starlite-saqlalchemy/commit/1781c7ae90057a163e1ab71f2dc182ecc56ea069))
* **config:** Add uvicorn/uvloop deps and configuration. ([`06b6036`](https://github.com/topsport-com-au/starlite-saqlalchemy/commit/06b6036fbc2ec0061e605b6b561955d918831c00))

## v0.6.0 (2022-11-14)
### Feature
* **config:** Support loading .env files. ([`9d3a505`](https://github.com/topsport-com-au/starlite-saqlalchemy/commit/9d3a505bb0e8823579105e0bee2b87434e280230))

## v0.5.0 (2022-11-13)
### Breaking
* flatten structure ([`2ba37be`](https://github.com/topsport-com-au/starlite-saqlalchemy/commit/2ba37be06e6b6879e196c3ec06b42f94def56071))
* move sqlalchemy config into `db` sub-package. ([`fd3b6f6`](https://github.com/topsport-com-au/starlite-saqlalchemy/commit/fd3b6f661438862552d9988ecda190d3856a80a0))

## v0.4.0 (2022-11-11)
### Feature
* **service:** Removes the service authorization methods. ([`e7fcc2d`](https://github.com/topsport-com-au/starlite-saqlalchemy/commit/e7fcc2d26a67b448ce0a44e63e91511dd57e513d))

### Breaking
* removes the service authorization methods. ([`e7fcc2d`](https://github.com/topsport-com-au/starlite-saqlalchemy/commit/e7fcc2d26a67b448ce0a44e63e91511dd57e513d))

### Documentation
* Tidy up. ([`e524edf`](https://github.com/topsport-com-au/starlite-saqlalchemy/commit/e524edf83dc7e6fc5257b3bea59a446c8e6cb888))

## v0.3.0 (2022-11-07)
### Feature
* **dto:** Dto.DTOField and dto.Mark. ([`ca47028`](https://github.com/topsport-com-au/starlite-saqlalchemy/commit/ca47028f674b696493564d07379b589756433cc1))

### Fix
* **log:** Fix dev config write to bytes logger. ([`2d8c69e`](https://github.com/topsport-com-au/starlite-saqlalchemy/commit/2d8c69ec93083d1d6dc42ebceb8e43b02cde9408))
* Removes static files config. ([`bdf5ea5`](https://github.com/topsport-com-au/starlite-saqlalchemy/commit/bdf5ea56d4f04f6fa7b907492d305417e48be9f1))

### Breaking
* dto.DTOField and dto.Mark. ([`ca47028`](https://github.com/topsport-com-au/starlite-saqlalchemy/commit/ca47028f674b696493564d07379b589756433cc1))
* removes static files config. ([`bdf5ea5`](https://github.com/topsport-com-au/starlite-saqlalchemy/commit/bdf5ea56d4f04f6fa7b907492d305417e48be9f1))

### Documentation
* Restructures and adds to documentation ([`2f8875c`](https://github.com/topsport-com-au/starlite-saqlalchemy/commit/2f8875ce10eb4e212bc184b8b5f0f48170f3b2d1))

## v0.2.0 (2022-11-05)
### Feature
* **worker:** Improves the worker pattern. ([#90](https://github.com/topsport-com-au/starlite-saqlalchemy/issues/90)) ([`32714a5`](https://github.com/topsport-com-au/starlite-saqlalchemy/commit/32714a5ca2329bca1d67770b388c4b984f815aaf))
* **logs:** Structlog configuration. ([#86](https://github.com/topsport-com-au/starlite-saqlalchemy/issues/86)) ([`7d87b96`](https://github.com/topsport-com-au/starlite-saqlalchemy/commit/7d87b965557c24e7c244af8a810fe67f12b60b5a))
* **testing:** Create a `testing` sub-package. ([#85](https://github.com/topsport-com-au/starlite-saqlalchemy/issues/85)) ([`9dfda10`](https://github.com/topsport-com-au/starlite-saqlalchemy/commit/9dfda10af09a679ae06aba12f24d8a57b105ae99))
* **response:** Makes serializer configurable. ([#84](https://github.com/topsport-com-au/starlite-saqlalchemy/issues/84)) ([`3439d26`](https://github.com/topsport-com-au/starlite-saqlalchemy/commit/3439d26e589f7c85f4676cca324ccdb728c2bfc3))
* **repository:** Make abc more general. ([#82](https://github.com/topsport-com-au/starlite-saqlalchemy/issues/82)) ([`9e89434`](https://github.com/topsport-com-au/starlite-saqlalchemy/commit/9e89434305d22bee1a0804c0d5c44d720fe3a939))

### Documentation
* **reference:** Fixes ref docs generation warning. ([#71](https://github.com/topsport-com-au/starlite-saqlalchemy/issues/71)) ([`1f04058`](https://github.com/topsport-com-au/starlite-saqlalchemy/commit/1f04058689636b0454500a1577a71e332f30aa66))
* **readme:** Fix badges. ([#69](https://github.com/topsport-com-au/starlite-saqlalchemy/issues/69)) ([`b9b3b3e`](https://github.com/topsport-com-au/starlite-saqlalchemy/commit/b9b3b3e4801abd0f5e6a2d966731ac373543b392))

## v0.1.8 (2022-10-30)
### Fix
* **worker:** Depend on typed SAQ ([#33](https://github.com/topsport-com-au/starlite-saqlalchemy/issues/33)) ([`13d3ac0`](https://github.com/topsport-com-au/starlite-saqlalchemy/commit/13d3ac00eaff1d288cfcf7c69e78e320f5937330))

### Documentation
* Header alignment and new badges ([#35](https://github.com/topsport-com-au/starlite-saqlalchemy/issues/35)) ([`3f8ff79`](https://github.com/topsport-com-au/starlite-saqlalchemy/commit/3f8ff79cd3291691aac66a9fdb1716106dd66a8d))

## v0.1.7 (2022-10-30)
### Fix
* **docs:** Removes patch version from docs tag ([#32](https://github.com/topsport-com-au/starlite-saqlalchemy/issues/32)) ([`ffcc647`](https://github.com/topsport-com-au/starlite-saqlalchemy/commit/ffcc6477ce59b8a3bd09b8377c50697aec231c5d))

## v0.1.6 (2022-10-30)
### Fix
* **docs:** Debug permissions issue ([#31](https://github.com/topsport-com-au/starlite-saqlalchemy/issues/31)) ([`4556dec`](https://github.com/topsport-com-au/starlite-saqlalchemy/commit/4556decf34e9a9886a165cd277eb42b5da9c0e31))

## v0.1.5 (2022-10-30)
### Fix
* **docs:** Passenv HOME for locating git config ([#30](https://github.com/topsport-com-au/starlite-saqlalchemy/issues/30)) ([`164ddf0`](https://github.com/topsport-com-au/starlite-saqlalchemy/commit/164ddf03d44366c0a3d4bdca53a0905275f8d77b))

## v0.1.4 (2022-10-30)
### Fix
* **docs:** Address docs build error ([#28](https://github.com/topsport-com-au/starlite-saqlalchemy/issues/28)) ([`07b7f0c`](https://github.com/topsport-com-au/starlite-saqlalchemy/commit/07b7f0ca668efcd8fc63a3d590e726faff432890))

## v0.1.3 (2022-10-30)
### Fix
* **build:** Remove invalid classifier ([#27](https://github.com/topsport-com-au/starlite-saqlalchemy/issues/27)) ([`76386a1`](https://github.com/topsport-com-au/starlite-saqlalchemy/commit/76386a135360b5b1f09413bd5920bae4c9591d70))

## v0.1.2 (2022-10-30)
### Fix
* **build:** Don't use GH action ([#26](https://github.com/topsport-com-au/starlite-saqlalchemy/issues/26)) ([`305f8e7`](https://github.com/topsport-com-au/starlite-saqlalchemy/commit/305f8e7b9f1de3a5e75823f30ab3d99cef26fbe6))

## v0.1.1 (2022-10-29)
### Fix
* **docs:** Use python 3.11 ([#25](https://github.com/topsport-com-au/starlite-saqlalchemy/issues/25)) ([`52d7f15`](https://github.com/topsport-com-au/starlite-saqlalchemy/commit/52d7f1526f94540a318142c72522a1deb2ffcb6d))

## v0.1.0 (2022-10-29)
### Feature
* Service object callback pattern ([#22](https://github.com/topsport-com-au/starlite-saqlalchemy/issues/22)) ([`b59c2d5`](https://github.com/topsport-com-au/starlite-saqlalchemy/commit/b59c2d5f8feee0dbb40d326258daacd28849b62a))

### Documentation
* Build on tag and use `github.ref_name` for version. ([#20](https://github.com/topsport-com-au/starlite-saqlalchemy/issues/20)) ([`d5733e3`](https://github.com/topsport-com-au/starlite-saqlalchemy/commit/d5733e3e1dbabd8991629afad7816bc42a572953))

## v0.0.1 (2022-10-24)
### Fix
- Starlite v1.32 compatibility ([#16](https://github.com/topsport-com-au/starlite-saqlalchemy/issues/16)) ([`2a84835`](https://github.com/topsport-com-au/starlite-saqlalchemy/commit/2a84835adfd2412403cecc9d33b6284990dc702f))
